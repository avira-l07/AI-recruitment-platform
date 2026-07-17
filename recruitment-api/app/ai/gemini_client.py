from app.core.time import utc_now
import json
import logging
import os
import re
import threading
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)
_health_lock = threading.Lock()
_health = {
    "configured": bool(os.getenv("GEMINI_API_KEY")),
    "status": "configured_not_tested" if os.getenv("GEMINI_API_KEY") else "not_configured",
    "last_success_at": None,
    "last_failure_at": None,
    "last_error_code": None,
    "last_error_message": None,
    "consecutive_failures": 0,
}


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    cleaned = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()
    try:
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else None
    except Exception:
        pass
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def _classify_error(error: Exception) -> tuple[str, str]:
    text = str(error).lower()
    if "429" in text or "quota" in text or "rate" in text:
        return "rate_limited", "Gemini quota or rate limit was reached."
    if "401" in text or "403" in text or "api key" in text or "permission" in text:
        return "authentication_failed", "Gemini authentication failed."
    if "timeout" in text or "timed out" in text:
        return "timeout", "Gemini request timed out."
    if "connection" in text or "unavailable" in text or "503" in text:
        return "temporarily_unavailable", "Gemini is temporarily unavailable."
    return "request_failed", "Gemini request failed."


def _record_success() -> None:
    with _health_lock:
        _health.update(
            {
                "configured": True,
                "status": "available",
                "last_success_at": utc_now(),
                "last_error_code": None,
                "last_error_message": None,
                "consecutive_failures": 0,
            }
        )


def _record_failure(code: str, message: str) -> None:
    with _health_lock:
        _health.update(
            {
                "configured": bool(os.getenv("GEMINI_API_KEY")),
                "status": code,
                "last_failure_at": utc_now(),
                "last_error_code": code,
                "last_error_message": message,
                "consecutive_failures": int(_health.get("consecutive_failures", 0)) + 1,
            }
        )


def get_gemini_health() -> Dict[str, Any]:
    with _health_lock:
        return dict(_health)


def call_gemini_json(prompt: str, model: str | None = None) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        _record_failure("not_configured", "Gemini API key is not configured.")
        return None

    selected_model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=selected_model, contents=prompt)
        parsed = extract_json(getattr(response, "text", ""))
        if parsed is None:
            _record_failure("invalid_response", "Gemini returned an invalid JSON response.")
            return None
        _record_success()
        return parsed
    except Exception as error:
        code, safe_message = _classify_error(error)
        _record_failure(code, safe_message)
        logger.warning("Gemini request failed with code=%s", code)
        return None
