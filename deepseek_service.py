from __future__ import annotations

import os
from typing import Any

import requests

from utils.logger import AppLogger

logger = AppLogger("deepseek_service").get_logger()


class DeepSeekService:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1/chat/completions")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    def generate_content(self, prompt: str) -> str:
        if not self.api_key:
            logger.warning("DeepSeek API key missing; using offline fallback content.")
            return self._fallback_response(prompt)

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a concise and practical travel planning assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.6,
        }

        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                logger.info("DeepSeek response generated successfully")
                return content.strip()
        except Exception as exc:  # pragma: no cover
            logger.warning("DeepSeek request failed: %s", exc)

        return self._fallback_response(prompt)

    def _fallback_response(self, prompt: str) -> str:
        if "itinerary" in prompt.lower():
            return "Create a balanced itinerary with morning, afternoon, and evening activities, keeping travel times reasonable."
        if "budget" in prompt.lower():
            return "Estimate moderate costs for lodging, meals, local transport, and entry fees, with a small contingency buffer."
        if "guide" in prompt.lower():
            return "Provide practical safety, packing, local customs, and emergency advice suited to the traveler profile."
        return "Provide concise, actionable travel advice using the destination and traveler profile."
