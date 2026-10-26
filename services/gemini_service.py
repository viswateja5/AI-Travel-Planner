from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib import error, request

from config import load_project_env
from utils.logger import AppLogger

logger = AppLogger("gemini_service").get_logger()


class GeminiProviderError(ValueError):
    def __init__(self, message: str, provider_status: int | None = None, timed_out: bool = False) -> None:
        super().__init__(message)
        self.provider_status = provider_status
        self.timed_out = timed_out

    @property
    def api_status_code(self) -> int:
        if self.timed_out or self.provider_status in {408, 504}:
            return 504
        if self.provider_status == 429 or (self.provider_status is not None and self.provider_status >= 500):
            return 503
        return 502


class GeminiService:
    SUPPORTED_MODELS = {
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.8-flash",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    }

    def __init__(self, api_key: str | None = None, model: str | None = None, timeout_seconds: int | None = None) -> None:
        load_project_env()
        key_value = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        model_value = model if model is not None else os.getenv("GEMINI_MODEL")
        self.api_key = (key_value or "").strip()
        self.model = self._validate_model(model_value or "gemini-3.5-flash-lite")
        timeout_value = timeout_seconds if timeout_seconds is not None else os.getenv("GEMINI_TIMEOUT_SECONDS", "90")
        try:
            self.timeout_seconds = int(str(timeout_value).strip() or "90")
        except ValueError:
            self.timeout_seconds = 90
        self.last_error: str | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _validate_model(self, model_name: str | None) -> str:
        normalized = (model_name or "gemini-3.5-flash-lite").strip()
        if normalized not in self.SUPPORTED_MODELS:
            raise ValueError(
                "Unsupported GEMINI_MODEL. Use gemini-3.5-flash-lite or gemini-3.8-flash."
            )
        return normalized

    def generate_content(self, prompt: str, max_output_tokens: int | None = None) -> str:
        if not self.api_key:
            self.last_error = "GEMINI_API_KEY is not configured. Add it to the project-root .env file before generating a trip."
            logger.warning("Gemini API key missing; no live generation attempted.")
            raise ValueError(self.last_error)

        token_limit = (
            max_output_tokens
            if max_output_tokens is not None
            else int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "1024"))
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": token_limit},
        }
        data = json.dumps(payload).encode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

        try:
            req = request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                method="POST",
            )
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                payload_response = json.loads(body)
                text = self._extract_text(payload_response)
                if not text:
                    raise ValueError("Gemini API returned an empty or malformed response.")
                logger.info("Gemini response generated successfully using model %s", self.model)
                return text.strip()
        except error.HTTPError as exc:
            provider_error = self._read_provider_error(exc, prompt)
            self.last_error = self._http_error_message(exc.code)
            self._log_failure(
                exc,
                self.last_error,
                http_status=exc.code,
                provider_error_body=provider_error,
            )
            raise GeminiProviderError(self.last_error, provider_status=exc.code) from exc
        except TimeoutError as exc:
            self.last_error = "Gemini request timed out while contacting the API."
            self._log_failure(exc, self.last_error)
            raise GeminiProviderError(self.last_error, timed_out=True) from exc
        except error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                self.last_error = "Gemini request timed out while contacting the API."
                self._log_failure(exc, self.last_error)
                raise GeminiProviderError(self.last_error, timed_out=True) from exc
            self.last_error = "Network failure while contacting Gemini. Check connectivity and try again."
            self._log_failure(exc, self.last_error)
            raise GeminiProviderError(self.last_error) from exc
        except OSError as exc:
            self.last_error = "Network failure while contacting Gemini. Check connectivity and try again."
            self._log_failure(exc, self.last_error)
            raise GeminiProviderError(self.last_error) from exc
        except (TypeError, ValueError, KeyError, IndexError, json.JSONDecodeError) as exc:
            self.last_error = "Gemini response was malformed or empty."
            self._log_failure(exc, self.last_error)
            raise ValueError(self.last_error) from exc
        except Exception as exc:  # pragma: no cover
            self.last_error = "Unexpected Gemini API error."
            self._log_failure(exc, self.last_error)
            raise ValueError(self.last_error) from exc

    def _log_failure(
        self,
        exc: Exception,
        safe_message: str,
        http_status: int | None = None,
        provider_error_body: dict[str, Any] | None = None,
    ) -> None:
        safe_body = json.dumps(provider_error_body, ensure_ascii=True, sort_keys=True) if provider_error_body else "unavailable"
        logger.error(
            "Gemini API request failed: exception_class=%s message=%s http_status=%s model=%s api_key_present=%s provider_error_body=%s",
            type(exc).__name__,
            safe_message,
            http_status if http_status is not None else "unavailable",
            self.model,
            self.is_configured,
            safe_body,
        )

    def _read_provider_error(self, exc: error.HTTPError, prompt: str) -> dict[str, Any]:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, OSError):
            return {"code": exc.code, "message": "Provider returned a non-JSON error body."}

        error_payload = payload.get("error") if isinstance(payload, dict) else None
        if not isinstance(error_payload, dict):
            return {"code": exc.code, "message": "Provider returned an unrecognized error body."}

        message_value = error_payload.get("message")
        message = message_value if isinstance(message_value, str) else "No provider error message."
        safe_message = self._sanitize_provider_message(message, prompt)

        sanitized: dict[str, Any] = {"code": exc.code, "message": safe_message}
        status = error_payload.get("status")
        if isinstance(status, str) and re.fullmatch(r"[A-Z_]{1,64}", status):
            sanitized["status"] = status
        return sanitized

    def _sanitize_provider_message(self, message: str, prompt: str) -> str:
        sanitized = message.replace(prompt, "[PROMPT REDACTED]") if prompt else message
        if self.api_key:
            sanitized = sanitized.replace(self.api_key, "[REDACTED]")
        sanitized = re.sub(
            r"(?i)(AIza[0-9A-Za-z_-]{20,}|bearer\s+\S+)",
            "[REDACTED]",
            sanitized,
        )
        sanitized = re.sub(r"(?i)(x-goog-api-key|authorization)\s*[:=]\s*\S+", r"\1=[REDACTED]", sanitized)
        return sanitized[:500]

    def _extract_text(self, payload_response: dict[str, Any]) -> str:
        candidates = payload_response.get("candidates") or []
        if not candidates:
            return ""
        first_candidate = candidates[0]
        content = first_candidate.get("content") or {}
        parts = content.get("parts") or []
        text_parts = []
        for part in parts:
            if isinstance(part, dict) and part.get("text"):
                text_parts.append(str(part["text"]))
        return "\n".join(text_parts).strip()

    def _http_error_message(self, status_code: int) -> str:
        if status_code in {400, 422}:
            return "Gemini rejected the generation request. Check the configured model and generation parameters."
        if status_code in {401, 403}:
            return "Invalid Gemini API key or authorization failed."
        if status_code == 429:
            return "Gemini API quota or rate limit exceeded."
        if status_code == 404:
            return "Configured Gemini model is unavailable. Choose a supported Gemini model."
        if status_code in {408, 504}:
            return "Gemini request timed out while contacting the API."
        if status_code >= 500:
            return "Gemini service is temporarily unavailable."
        return "Gemini request failed due to an unexpected provider error."
