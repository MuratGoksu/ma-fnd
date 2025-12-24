# agents/judge_agent.py
# LLM-based judge agent for detailed evaluation
import os
import json
from openai import OpenAI

class LLMJudgeAgent:
    """Uses an OpenAI LLM to evaluate pro/con arguments and return a structured verdict."""

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for LLMJudgeAgent")
        self.client = OpenAI(api_key=api_key)

    def evaluate_detailed(self, pro_arg: str, con_arg: str) -> dict:
        """Return verdict + confidence + rationale."""
        prompt = f"""
You are an impartial fact-checking analyst. 
Given the following supporting and opposing arguments, decide if the claim is REAL, FAKE, or UNSURE.
Respond in strict JSON with keys: verdict, confidence (0-1 float), rationale.

Supporting argument:
{pro_arg}

Opposing argument:
{con_arg}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a logical truth evaluator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=250
            )
            content = response.choices[0].message.content.strip()
            try:
                data = json.loads(content)
            except Exception:
                data = {"verdict": "UNSURE", "confidence": 0.5, "rationale": content}
            data["model"] = self.model
            return data
        except Exception as e:
            print(f"[error] LLMJudgeAgent failed: {e}")
            return {"verdict": "UNSURE", "confidence": 0.0, "rationale": str(e), "model": self.model}