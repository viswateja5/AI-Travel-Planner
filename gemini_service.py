from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request

from utils.logger import AppLogger

logger = AppLogger("gemini_service").get_logger()


class GeminiService:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    def generate_content(self, prompt: str) -> str:
        if not self.api_key:
            logger.warning("Gemini API key missing; using offline fallback content.")
            return self._fallback_response(prompt)

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.6},
        }
        data = json.dumps(payload).encode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"

        try:
            req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with request.urlopen(req, timeout=30) as response:
                body = response.read().decode("utf-8")
                payload_response = json.loads(body)
                candidates = payload_response.get("candidates", [])
                if candidates:
                    text = candidates[0]["content"]["parts"][0]["text"]
                    logger.info("Gemini response generated successfully")
                    return text
        except error.HTTPError as exc:
            logger.exception("Gemini API request failed with HTTP error: %s", exc)
        except Exception as exc:  # pragma: no cover
            logger.exception("Gemini API request failed: %s", exc)

        return self._fallback_response(prompt)

    def _fallback_response(self, prompt: str) -> str:
        if "itinerary" in prompt.lower():
            return "Create a balanced itinerary with morning, afternoon, and evening activities, keeping travel times reasonable."
        if "budget" in prompt.lower():
            return "Estimate moderate costs for lodging, meals, local transport, and entry fees, with a small contingency buffer."
        if "guide" in prompt.lower():
            return "Provide practical safety, packing, local customs, and emergency advice suited to the traveler profile."
        return "Provide concise, actionable travel advice using the destination and traveler profile."
