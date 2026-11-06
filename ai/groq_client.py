import json
import os
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

class GroqClient:
    """Interacts with the Groq Cloud API for intelligent speech disambiguation and intent refinement."""

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "").strip()
        self.model = model
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def set_api_key(self, api_key: str):
        self.api_key = api_key.strip()

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    def disambiguate_query(
        self,
        spoken_text: str,
        memory_websites: Optional[list] = None,
        recent_searches: Optional[list] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Uses Groq LLM to interpret ambiguous or phonetically corrupted voice queries,
        mapping them to intentional web searches, URLs, or file operations.
        Returns dict with keys: 'interpreted', 'is_url', 'target_url', 'explanation'
        """
        if not self.is_available() or not spoken_text.strip():
            return None

        sites_context = []
        if memory_websites:
            for s in memory_websites[:8]:
                sites_context.append(f"{s.get('name')}: {s.get('url')}")

        searches_context = recent_searches[:5] if recent_searches else []

        system_prompt = (
            "You are P.H.O.E.N.I.X. AI Assistant's speech disambiguation engine on Windows. "
            "The user spoke a command to an offline speech recognizer, which may have phonetic misspellings "
            "or domain naming blurs (e.g. 'chat gpt dot com' -> 'https://chatgpt.com', 'you tube' -> 'YouTube'). "
            "Determine what the user intended to search or open. "
            "Return valid JSON ONLY with this exact structure:\n"
            "{\n"
            '  "interpreted": "cleaned query or site name",\n'
            '  "is_url": true or false,\n'
            '  "target_url": "url if is_url is true, otherwise empty",\n'
            '  "confidence": 0.0 to 1.0\n'
            "}"
        )

        user_content = (
            f"Spoken text: '{spoken_text}'\n"
            f"User's frequent websites: {json.dumps(sites_context)}\n"
            f"Recent searches: {json.dumps(searches_context)}\n"
            "Valid drives: C, D, E.\n"
            "Respond in JSON only."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.1,
            "max_tokens": 150,
            "response_format": {"type": "json_object"}
        }

        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "PHOENIX-Agent/1.1"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                result = json.loads(choice)
                return result
        except Exception as e:
            # Non-blocking: fail gracefully if offline or invalid key
            print(f"[Groq AI] Disambiguation skipped/failed: {e}")
            return None
