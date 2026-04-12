import requests
import random
import re
import json


OLLAMA_URL = "http://localhost:11434"
MODEL = "llama3"


# ========== QUESTION GENERATOR ==========
def generate_question(topic, previous_answer=None, history=None, asked_questions=None):
    """
    Generate natural, conversational interview questions.
    Uses the full conversation history so the model actually listens.
    """
    if history is None:
        history = []
    if asked_questions is None:
        asked_questions = []

    question_count = len(asked_questions)

    # ── Opening question (no previous answer yet) ──
    if previous_answer is None:
        return (
            f"Hi, welcome! Thanks for coming in today. "
            f"Let's start simple — can you tell me a bit about yourself and your background in {topic}?"
        )

    # ── Build conversation context for the LLM ──
    convo_lines = []
    for msg in history[-8:]:  # last 8 messages for context window
        if isinstance(msg, dict):
            role = "Interviewer" if msg.get("role") == "ai" else "Candidate"
            convo_lines.append(f"{role}: {msg.get('text', '')}")
        elif isinstance(msg, str):
            convo_lines.append(msg)

    conversation_so_far = "\n".join(convo_lines) if convo_lines else "(conversation just started)"

    # ── Build the prompt ──
    prompt = f"""You are Alex, a friendly but sharp HR interviewer at a tech company.
You are interviewing a candidate for a {topic} role.

Here is the conversation so far:
{conversation_so_far}

The candidate just said:
"{previous_answer}"

Your job: Ask ONE short, natural follow-up question.

Rules:
- Sound like a real human interviewer, not a quiz machine
- Reference something SPECIFIC the candidate just said
- Do NOT repeat any previous question
- Do NOT evaluate or give feedback — just ask a question
- Keep it to 1-2 sentences max
- Use casual, warm language: "Oh interesting, so...", "Got it — what about...", "Tell me more about...", "How did that go?", "What happened next?"
- If they mentioned a project, ask about it
- If they mentioned a challenge, ask how they resolved it
- If their answer was vague, ask them to give a concrete example
- Do NOT start with "Great!", "Excellent!", "Wonderful!" or similar hollow praise

Respond with ONLY the question. No preamble, no label, nothing else."""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.85,
                    "top_p": 0.9,
                    "num_predict": 80,
                }
            },
            timeout=30
        )
        result = response.json().get("response", "").strip()
        question = result.split("\n")[0].strip()

        if not question:
            return _fallback_question(previous_answer, topic)

        if "?" not in question:
            question = question.rstrip(".") + "?"

        # Avoid near-duplicate questions
        for prev_q in (asked_questions or [])[-3:]:
            if question.lower()[:40] == prev_q.lower()[:40]:
                return _fallback_question(previous_answer, topic)

        print(f"[Q{question_count}] {question}")
        return question

    except Exception as e:
        print(f"[ai_engine] generate_question error: {e}")
        return _fallback_question(previous_answer, topic)


def _fallback_question(answer, topic):
    answer_lower = answer.lower()
    if "challenge" in answer_lower or "difficult" in answer_lower or "problem" in answer_lower:
        return "How did you end up resolving that?"
    elif "team" in answer_lower or "colleague" in answer_lower:
        return "What was your specific role in that team?"
    elif "project" in answer_lower or "built" in answer_lower or "developed" in answer_lower:
        return "What was the biggest technical decision you made on that project?"
    elif "learned" in answer_lower or "realized" in answer_lower:
        return "How did that change the way you approach things now?"
    else:
        return f"Can you give me a concrete example of that in your {topic} work?"


# ========== ANSWER EVALUATOR ==========
def evaluate_answer(question, answer):
    """
    Evaluate the candidate's answer and return natural interviewer feedback.
    Returns a dict: { score, feedback, strength, area_to_improve }
    """

    if not answer or len(answer.strip()) < 15:
        return {
            "score": 2,
            "feedback": "Hmm, I need a bit more to go on there. Can you expand on that?",
            "strength": "Attempted to answer",
            "area_to_improve": "Provide more detail and context"
        }

    prompt = f"""You are Alex, a friendly but sharp HR interviewer.
The candidate just answered your interview question.

Your Question: {question}
Candidate's Answer: {answer}

Evaluate the answer honestly. Then write a SHORT, NATURAL interviewer reaction — the kind of thing a real person says mid-interview.

Rules for your reaction:
- 1-3 sentences MAX
- Sound natural and human — like you're actually listening
- Do NOT use hollow openers like "Great!", "Excellent!", "Wonderful!"
- If the answer is strong, acknowledge it briefly and move on
- If the answer is weak or vague, gently push back or note what's missing
- Reference something SPECIFIC they said
- Use casual, warm language

Then provide a JSON object on a new line (and ONLY JSON after that) in this exact format:
{{"score": <integer 1-10>, "strength": "<one phrase>", "area_to_improve": "<one phrase>"}}

Example output:
Yeah, that makes sense — I like that you mentioned the actual impact on load times. Good example.
{{"score": 8, "strength": "Concrete metrics included", "area_to_improve": "Could mention team collaboration"}}"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150,
                }
            },
            timeout=30
        )
        raw = response.json().get("response", "").strip()
        print(f"[evaluate_answer raw] {raw}")

        # Split feedback text from JSON
        lines = [l.strip() for l in raw.split("\n") if l.strip()]
        feedback_lines = []
        json_data = None

        for line in lines:
            if line.startswith("{"):
                try:
                    json_data = json.loads(line)
                    break
                except Exception:
                    pass
            else:
                feedback_lines.append(line)

        feedback = " ".join(feedback_lines).strip()
        if not feedback:
            feedback = _fallback_feedback(answer)

        score = 5
        strength = "Relevant answer given"
        area = "Add more specific examples"

        if json_data:
            score = max(1, min(10, int(json_data.get("score", 5))))
            strength = json_data.get("strength", strength)
            area = json_data.get("area_to_improve", area)
        else:
            score = _heuristic_score(answer)

        return {
            "score": score,
            "feedback": feedback,
            "strength": strength,
            "area_to_improve": area
        }

    except Exception as e:
        print(f"[ai_engine] evaluate_answer error: {e}")
        return {
            "score": 5,
            "feedback": _fallback_feedback(answer),
            "strength": "Answer provided",
            "area_to_improve": "Try to include specific examples and outcomes"
        }


def _fallback_feedback(answer):
    answer_lower = answer.lower()
    if any(w in answer_lower for w in ["challenge", "difficult", "problem"]):
        return "I can see you've dealt with some tough situations. How did that turn out in the end?"
    elif any(w in answer_lower for w in ["team", "collaborate", "worked with"]):
        return "Okay, sounds like teamwork was key there. Good."
    elif len(answer.split()) < 30:
        return "Alright, I'd love a bit more detail on that if you have it."
    else:
        return "Got it, thanks for walking me through that."


def _heuristic_score(answer):
    score = 4
    a = answer.lower()
    if re.search(r'\d+%|\d+\s*(users|months|years|days|hours|engineers|projects)', a):
        score += 2
    if any(w in a for w in ["result", "achieved", "delivered", "outcome", "impact"]):
        score += 1.5
    if any(w in a for w in ["challenge", "problem", "obstacle"]):
        score += 1
    if any(w in a for w in ["learned", "improved", "realized"]):
        score += 0.5
    if len(answer.split()) > 100:
        score += 0.5
    return round(min(10, score), 1)