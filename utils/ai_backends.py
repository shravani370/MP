"""
utils/ai_backends.py — Multi-backend AI abstraction layer
Supports: Ollama (local), OpenAI, Anthropic, Google Gemini
"""
import os
import json
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# AI BACKEND FACTORY
# ═══════════════════════════════════════════════════════════════════════════

class AIBackend:
    """Base class for AI backends"""
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        raise NotImplementedError
    
    def evaluate(self, question: str, answer: str) -> Dict[str, Any]:
        """Evaluate answer to question, return JSON with score, feedback, etc."""
        raise NotImplementedError
    
    def health_check(self) -> bool:
        """Check if backend is available"""
        raise NotImplementedError


class OllamaBackend(AIBackend):
    """Local Ollama instance backend"""
    
    def __init__(self):
        self.url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = os.environ.get("OLLAMA_MODEL", "llama2")
        self.timeout = 120
    
    def health_check(self) -> bool:
        try:
            resp = requests.get(f"{self.url.replace('/api/generate', '')}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        try:
            # Add JSON constraint if available in model and requested
            payload = {
                "model": self.model, 
                "prompt": prompt, 
                "stream": False,
                "temperature": kwargs.get("temperature", 0.3),  # Lower temp for consistency
            }
            
            # Optional: add format constraint for newer Ollama versions
            # Uncomment if your Ollama supports it
            # payload["format"] = "json"
            
            resp = requests.post(
                self.url,
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            response_text = resp.json().get("response", "").strip()
            
            if not response_text:
                logger.warning("Ollama returned empty response")
                return "{}"
            
            return response_text
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
            return f"[Ollama error: {e}]"
    
    def evaluate(self, question: str, answer: str) -> Dict[str, Any]:
        prompt = f"""You are a technical interview evaluator.
Evaluate based on current (2026) best practices.

Question: {question}
Answer: {answer}

Respond in valid JSON only (no markdown):
{{
  "score": <1-10 integer>,
  "strengths": "<short strength>",
  "improvements": "<area to improve>",
  "verdict": "Excellent|Good|Average|Poor"
}}"""
        raw = self.generate(prompt)
        
        # Try multiple JSON parsing strategies
        result = None
        
        # Strategy 1: Direct parse
        try:
            result = json.loads(raw)
        except Exception:
            pass
        
        # Strategy 2: Extract from markdown
        if not result:
            try:
                clean = raw.strip()
                if "```" in clean:
                    clean = clean.split("```")[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
                result = json.loads(clean.strip())
            except Exception:
                pass
        
        # Strategy 3: Find and extract JSON object
        if not result:
            try:
                start = raw.index("{")
                end = raw.rindex("}") + 1
                result = json.loads(raw[start:end])
            except Exception:
                pass
        
        # Fallback if all parsing failed
        if not result:
            logger.warning(f"Ollama evaluation parse failed: {raw}")
            result = {
                "score": 5,
                "strengths": "Answer provided",
                "improvements": "Could not evaluate - AI response parsing failed",
                "verdict": "Average",
            }
        
        return result


class OpenAIBackend(AIBackend):
    """OpenAI API backend"""
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set")
        self.model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
        self.timeout = 30
    
    def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            import openai
            openai.api_key = self.api_key
            # Try a minimal API call
            openai.Model.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        try:
            import openai
            openai.api_key = self.api_key
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                timeout=self.timeout
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI generation failed: {e}")
            return f"[OpenAI error: {e}]"
    
    def evaluate(self, question: str, answer: str) -> Dict[str, Any]:
        prompt = f"""You are a technical interview evaluator.
Evaluate based on current (2026) best practices.

Question: {question}
Answer: {answer}

Respond in valid JSON only (no markdown):
{{
  "score": <1-10 integer>,
  "strengths": "<short strength>",
  "improvements": "<area to improve>",
  "verdict": "Excellent|Good|Average|Poor"
}}"""
        raw = self.generate(prompt, temperature=0)
        
        # Try multiple JSON parsing strategies
        result = None
        
        # Strategy 1: Direct parse
        try:
            result = json.loads(raw)
        except Exception:
            pass
        
        # Strategy 2: Extract from markdown
        if not result:
            try:
                clean = raw.strip()
                if "```" in clean:
                    clean = clean.split("```")[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
                result = json.loads(clean.strip())
            except Exception:
                pass
        
        # Strategy 3: Find and extract JSON object
        if not result:
            try:
                start = raw.index("{")
                end = raw.rindex("}") + 1
                result = json.loads(raw[start:end])
            except Exception:
                pass
        
        # Fallback if all parsing failed
        if not result:
            logger.warning(f"OpenAI evaluation parse failed: {raw}")
            result = {
                "score": 5,
                "strengths": "Answer provided",
                "improvements": "Could not evaluate - AI response parsing failed",
                "verdict": "Average",
            }
        
        return result


class AnthropicBackend(AIBackend):
    """Anthropic Claude API backend"""
    
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not set")
        self.model = os.environ.get("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        self.timeout = 30
    
    def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            import anthropic  # type: ignore
            client = anthropic.Anthropic(api_key=self.api_key)
            # Minimal API call to verify credentials
            client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception as e:
            logger.warning(f"Anthropic health check failed: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        try:
            import anthropic  # type: ignore
            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.warning(f"Anthropic generation failed: {e}")
            return f"[Anthropic error: {e}]"
    
    def evaluate(self, question: str, answer: str) -> Dict[str, Any]:
        prompt = f"""You are a technical interview evaluator.
Evaluate based on current (2026) best practices.

Question: {question}
Answer: {answer}

Respond in valid JSON only (no markdown):
{{
  "score": <1-10 integer>,
  "strengths": "<short strength>",
  "improvements": "<area to improve>",
  "verdict": "Excellent|Good|Average|Poor"
}}"""
        raw = self.generate(prompt)
        
        # Try multiple JSON parsing strategies
        result = None
        
        # Strategy 1: Direct parse
        try:
            result = json.loads(raw)
        except Exception:
            pass
        
        # Strategy 2: Extract from markdown
        if not result:
            try:
                clean = raw.strip()
                if "```" in clean:
                    clean = clean.split("```")[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
                result = json.loads(clean.strip())
            except Exception:
                pass
        
        # Strategy 3: Find and extract JSON object
        if not result:
            try:
                start = raw.index("{")
                end = raw.rindex("}") + 1
                result = json.loads(raw[start:end])
            except Exception:
                pass
        
        # Fallback if all parsing failed
        if not result:
            logger.warning(f"Anthropic evaluation parse failed: {raw}")
            result = {
                "score": 5,
                "strengths": "Answer provided",
                "improvements": "Could not evaluate - AI response parsing failed",
                "verdict": "Average",
            }
        
        return result


class GeminiBackend(AIBackend):
    """Google Gemini API backend"""
    
    def __init__(self):
        self.api_key = os.environ.get("GOOGLE_GENAI_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_GENAI_API_KEY not set")
        self.model = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
        self.timeout = 30
    
    def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            model.generate_content("Hi", stream=False)
            return True
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt, stream=False)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini generation failed: {e}")
            return f"[Gemini error: {e}]"
    
    def evaluate(self, question: str, answer: str) -> Dict[str, Any]:
        prompt = f"""You are a technical interview evaluator.
Evaluate based on current (2026) best practices.

Question: {question}
Answer: {answer}

Respond in valid JSON only (no markdown):
{{
  "score": <1-10 integer>,
  "strengths": "<short strength>",
  "improvements": "<area to improve>",
  "verdict": "Excellent|Good|Average|Poor"
}}"""
        raw = self.generate(prompt)
        
        # Try multiple JSON parsing strategies
        result = None
        
        # Strategy 1: Direct parse
        try:
            result = json.loads(raw)
        except Exception:
            pass
        
        # Strategy 2: Extract from markdown
        if not result:
            try:
                clean = raw.strip()
                if "```" in clean:
                    clean = clean.split("```")[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
                result = json.loads(clean.strip())
            except Exception:
                pass
        
        # Strategy 3: Find and extract JSON object
        if not result:
            try:
                start = raw.index("{")
                end = raw.rindex("}") + 1
                result = json.loads(raw[start:end])
            except Exception:
                pass
        
        # Fallback if all parsing failed
        if not result:
            logger.warning(f"Gemini evaluation parse failed: {raw}")
            result = {
                "score": 5,
                "strengths": "Answer provided",
                "improvements": "Could not evaluate - AI response parsing failed",
                "verdict": "Average",
            }
        
        return result


# ═══════════════════════════════════════════════════════════════════════════
# AI MANAGER — AUTO-SELECT BEST AVAILABLE BACKEND
# ═══════════════════════════════════════════════════════════════════════════

class AIManager:
    """Smart backend selector that tries backends in priority order"""
    
    def __init__(self):
        self.backends = {}
        self.current_backend = None
        self._init_backends()
    
    def _init_backends(self):
        """Initialize all available backends"""
        backends_to_try = [
            ("openai", OpenAIBackend),
            ("anthropic", AnthropicBackend),
            ("gemini", GeminiBackend),
            ("ollama", OllamaBackend),
        ]
        
        for name, backend_class in backends_to_try:
            try:
                backend = backend_class()
                self.backends[name] = backend
                logger.info(f"Initialized {name} backend")
            except Exception as e:
                logger.warning(f"Failed to init {name}: {e}")
        
        # Auto-select first available backend
        self._select_best_backend()
    
    def _select_best_backend(self):
        """Select the best available backend"""
        priority_order = ["openai", "anthropic", "gemini", "ollama"]
        
        for backend_name in priority_order:
            if backend_name in self.backends:
                backend = self.backends[backend_name]
                if backend.health_check():
                    self.current_backend = backend
                    logger.info(f"Selected {backend_name} as active AI backend")
                    return
        
        # Fallback: use Ollama even if not responding
        if "ollama" in self.backends:
            self.current_backend = self.backends["ollama"]
            logger.warning("Using Ollama backend (may not be available)")
            return
        
        raise RuntimeError("No AI backend available. Configure OpenAI, Anthropic, Gemini API key or start Ollama.")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using current backend"""
        if not self.current_backend:
            return "[No AI backend configured]"
        return self.current_backend.generate(prompt, **kwargs)
    
    def evaluate(self, question: str, answer: str) -> Dict[str, Any]:
        """Evaluate answer using current backend"""
        if not self.current_backend:
            return {
                "score": 0,
                "strengths": "N/A",
                "improvements": "No AI backend available",
                "verdict": "N/A",
            }
        return self.current_backend.evaluate(question, answer)
    
    def status(self) -> Dict[str, Any]:
        """Get status of all backends"""
        return {
            "current": self.current_backend.__class__.__name__ if self.current_backend else None,
            "available": {name: backend.health_check() for name, backend in self.backends.items()}
        }


# Global instance
_ai_manager = None

def get_ai_manager() -> AIManager:
    """Get or create global AI manager"""
    global _ai_manager
    if _ai_manager is None:
        _ai_manager = AIManager()
    return _ai_manager
