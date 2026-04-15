"""
utils/ai_engine.py — AI Engine (backward-compatible wrapper)
The main logic now lives in app.py. This module keeps compatibility
if any other file imports from here.
"""
import requests
import os
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")


def _ollama(prompt: str) -> str:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as e:
        logger.warning(f"Ollama call failed: {e}")
        return "[AI unavailable – start Ollama: `ollama serve`]"


def generate_question(
    topic: str,
    previous_answer: str = "",
    history: list = None,
    asked_questions: list = None,
) -> str:
    asked_str = "\n".join(asked_questions or [])
    history_str = "\n".join(history or [])
    prompt = f"""You are a senior technical interviewer specialising in {topic} (as of 2026).
Focus on LATEST industry practices, modern frameworks, and current best practices.
Generate ONE concise, relevant interview question that tests current knowledge.

Do NOT repeat any question from this list:
{asked_str}

Previous conversation:
{history_str}

Candidate's last answer: {previous_answer}

Return ONLY the question text."""
    return _ollama(prompt)


def evaluate_answer(question: str, answer: str) -> dict:
    prompt = f"""You are a technical interview evaluator assessing 2026-standard practices.
Evaluate based on LATEST industry best practices and current understanding.

Question: {question}
Answer: {answer}

Evaluate and respond in valid JSON with keys:
- score: integer 1-10 (based on current best practices)
- strengths: short string
- improvements: short string (based on current standards)
- verdict: "Excellent" | "Good" | "Average" | "Poor"
"""
    raw = _ollama(prompt)
    try:
        clean = raw.strip().lstrip("```json").rstrip("```").strip()
        return json.loads(clean)
    except Exception:
        return {
            "score": 5,
            "strengths": "Answer provided",
            "improvements": raw or "Could not evaluate",
            "verdict": "Average",
        }


def generate_mcq_questions(role: str, n: int = 10) -> list:
    """Generate MCQ questions for a given role using AI."""
    prompt = f"""You are a technical recruiter creating {n} multiple-choice screening questions for a {role} position in 2026.
Use LATEST industry standards, best practices, and current technologies. Focus on modern approaches and frameworks.

Generate EXACTLY {n} questions in valid JSON array format. Each question MUST have these exact fields:
- "q": the question text (string)
- "options": exactly 4 answer options (array of strings) - list CORRECT answer FIRST
- "answer": the index 0-3 of the correct answer (integer) - make sure it points to the LATEST CORRECT answer

IMPORTANT: The correct answer should reflect CURRENT best practices (2026), not outdated information.

Example format:
[
  {{"q": "Question 1?", "options": ["opt1_CORRECT", "opt2_old", "opt3", "opt4"], "answer": 0}},
  {{"q": "Question 2?", "options": ["opt1_CORRECT", "opt2", "opt3_old", "opt4"], "answer": 0}}
]

Return ONLY the JSON array, no markdown, no text before or after."""
    
    raw = _ollama(prompt)
    try:
        # Try to extract JSON from the response
        clean = raw.strip()
        
        # Remove markdown code blocks if present
        if "```" in clean:
            parts = clean.split("```")
            for part in parts:
                if part.strip().startswith("["):
                    clean = part.strip()
                    break
        
        # Remove leading/trailing whitespace and markers
        if clean.startswith("json"):
            clean = clean[4:].strip()
        if clean.startswith("["):
            # Find the first [ and last ]
            start = clean.find("[")
            end = clean.rfind("]")
            if start >= 0 and end > start:
                clean = clean[start:end+1]
        
        questions = json.loads(clean)
        
        # Validate structure
        validated = []
        for q in questions:
            if isinstance(q, dict):
                # Try to get required fields
                q_text = q.get("q") or q.get("question")
                options = q.get("options")
                answer = q.get("answer")
                
                if q_text and options and answer is not None:
                    if isinstance(options, list) and len(options) == 4:
                        if isinstance(answer, int) and 0 <= answer < 4:
                            validated.append({
                                "q": q_text,
                                "options": options,
                                "answer": answer
                            })
        
        # Return validated questions
        if validated:
            return validated[:n]
        
        logger.warning(f"MCQ validation failed for {role}, got {len(questions)} questions but none validated")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"MCQ JSON decode error for {role}: {e}\nRaw response: {raw[:200]}")
        return []
    except Exception as e:
        logger.error(f"MCQ generation error for {role}: {e}")
        return []


def generate_coding_questions(role: str, n: int = 2) -> list:
    """Generate coding challenge questions for a given role using AI."""
    prompt = f"""You are a technical interviewer creating {n} coding challenges for a {role} position in 2026.
Use LATEST technologies, frameworks, and best practices. Focus on real-world relevance and modern approaches.

Generate EXACTLY {n} challenges in valid JSON array format. Each challenge MUST have:
- "id": unique identifier (string, snake_case)
- "func": function name to implement (string)
- "title": challenge title (string)
- "difficulty": "Easy" or "Medium" (string)
- "description": problem description with example using LATEST practices (string, can include newlines)
- "starter": Python function stub starting with def (string)
- "test_cases": array of objects with "input" (tuple) and "expected" (expected result)

Example:
[
  {{
    "id": "two_sum",
    "func": "two_sum",
    "title": "Two Sum Problem",
    "difficulty": "Easy",
    "description": "Find two numbers that add to target.",
    "starter": "def two_sum(nums, target):\\n    pass",
    "test_cases": [
      {{"input": ([1, 2, 3], 5), "expected": [1, 2]}},
      {{"input": ([1, 2], 3), "expected": [0, 1]}}
    ]
  }}
]

Return ONLY the JSON array, no markdown, no explanation."""
    
    raw = _ollama(prompt)
    try:
        # Try to extract JSON from the response
        clean = raw.strip()
        
        # Remove markdown code blocks if present
        if "```" in clean:
            parts = clean.split("```")
            for part in parts:
                if part.strip().startswith("["):
                    clean = part.strip()
                    break
        
        # Remove leading markers
        if clean.startswith("json"):
            clean = clean[4:].strip()
        
        if clean.startswith("["):
            # Find the first [ and last ]
            start = clean.find("[")
            end = clean.rfind("]")
            if start >= 0 and end > start:
                clean = clean[start:end+1]
        
        questions = json.loads(clean)
        
        # Validate structure
        validated = []
        for q in questions:
            if isinstance(q, dict):
                required_fields = ["id", "func", "title", "difficulty", "description", "starter", "test_cases"]
                if all(field in q for field in required_fields):
                    if isinstance(q.get("test_cases"), list) and len(q["test_cases"]) >= 2:
                        validated.append({
                            "id": str(q["id"]),
                            "func": str(q["func"]),
                            "title": str(q["title"]),
                            "difficulty": str(q["difficulty"]),
                            "description": str(q["description"]),
                            "starter": str(q["starter"]),
                            "test_cases": q["test_cases"]
                        })
        
        # Return validated questions
        if validated:
            return validated[:n]
        
        logger.warning(f"Coding validation failed for {role}, got {len(questions)} questions but none validated")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Coding JSON decode error for {role}: {e}\nRaw response: {raw[:200]}")
        return []
    except Exception as e:
        logger.error(f"Coding generation error for {role}: {e}")
        return []