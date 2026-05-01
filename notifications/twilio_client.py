"""Direct Twilio sender used by the 7:30 PM notification job (no LLM).

Returns True on success, False on failure (errors logged but never raised).
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

TIMEOUT = httpx.Timeout(15.0, connect=5.0)


def _twilio_url() -> str:
    return f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"


def _auth() -> tuple:
    return (settings.twilio_account_sid, settings.twilio_auth_token)


async def _send(payload: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(_twilio_url(), data=payload, auth=_auth())
        if response.status_code == 201:
            sid = response.json().get("sid", "")
            logger.info("twilio sent (sid=%s)", sid)
            return True
        logger.error("twilio failed status=%d body=%s", response.status_code, response.text[:300])
        return False
    except Exception:  # noqa: BLE001
        logger.exception("twilio exception")
        return False


async def send_twilio_notification(message: str, channel: Optional[str] = None) -> bool:
    """Send a notification via WhatsApp (default) or SMS, with WhatsApp->SMS fallback."""
    issues = settings.validate_twilio()
    if issues:
        logger.warning("twilio not configured: %s", [i.field for i in issues])
        return False

    target_channel = channel or settings.twilio_channel

    if target_channel == "whatsapp":
        ok = await _send({
            "From": f"whatsapp:{settings.twilio_from_number}",
            "To": f"whatsapp:{settings.twilio_to_number}",
            "Body": message,
        })
        if ok:
            return True
        logger.info("WhatsApp failed, falling back to SMS")

    return await _send({
        "From": settings.twilio_from_number,
        "To": settings.twilio_to_number,
        "Body": message,
    })
