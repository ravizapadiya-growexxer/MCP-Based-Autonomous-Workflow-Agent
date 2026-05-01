"""
WhatsApp notifications via:
  Primary:  CallMeBot API (free, personal use)
  Fallback: Twilio WhatsApp Business API (paid)

CallMeBot Setup (one-time, ~2 minutes):
  1. Add +34 644 59 71 28 to WhatsApp contacts (name: CallMeBot)
  2. Send this message: "I allow callmebot to send me messages"
  3. You'll receive an API key via WhatsApp within 60 seconds
  4. Set WHATSAPP_PHONE and WHATSAPP_APIKEY in .env
"""

from __future__ import annotations
import urllib.parse
import httpx
from loguru import logger
from config.settings import settings


async def send_whatsapp(message: str) -> bool:
    """Send a WhatsApp message. Returns True on success."""
    # Try CallMeBot first
    if settings.whatsapp_phone and settings.whatsapp_apikey:
        success = await _send_callmebot(message)
        if success:
            return True
        logger.warning("CallMeBot failed, trying Twilio...")

    # Try Twilio
    if settings.twilio_account_sid and settings.twilio_auth_token:
        return await _send_twilio(message)

    logger.warning("No WhatsApp provider configured — message not sent")
    return False


async def _send_callmebot(message: str) -> bool:
    """Send via CallMeBot free API."""
    url = "https://api.callmebot.com/whatsapp.php"
    params = {
        "phone": settings.whatsapp_phone,
        "text": message,
        "apikey": settings.whatsapp_apikey,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url, params=params)
            if r.status_code == 200 and "Message queued" in r.text:
                logger.info("WhatsApp (CallMeBot) sent successfully")
                return True
            logger.warning(f"CallMeBot response: {r.status_code} — {r.text[:100]}")
            return False
    except Exception as exc:
        logger.error(f"CallMeBot error: {exc}")
        return False


async def _send_twilio(message: str) -> bool:
    """Send via Twilio WhatsApp API."""
    try:
        from twilio.rest import Client
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        msg = client.messages.create(
            body=message,
            from_=settings.twilio_whatsapp_from,
            to=settings.twilio_whatsapp_to,
        )
        logger.info(f"WhatsApp (Twilio) sent: sid={msg.sid}")
        return True
    except ImportError:
        logger.warning("twilio package not installed — pip install twilio")
        return False
    except Exception as exc:
        logger.error(f"Twilio error: {exc}")
        return False


def fmt_morning_success(story_key: str, subtask_key: str, subtask_title: str) -> str:
    return (
        f"✅ *Morning Workflow Done*\n"
        f"Story: {story_key}\n"
        f"Subtask: {subtask_key} — {subtask_title}\n"
        f"Status: In Progress\n"
        f"Estimate: 8h set"
    )


def fmt_evening_success(story_key: str, timesheet_synced: bool) -> str:
    ts_status = "✅ Synced" if timesheet_synced else "⚠️ Failed"
    return (
        f"✅ *Evening Workflow Done*\n"
        f"Story: {story_key} → Done\n"
        f"Worklog: 8h logged\n"
        f"Timesheet: {ts_status}"
    )


def fmt_error(phase: str, error: str) -> str:
    return (
        f"🚨 *{phase.capitalize()} Workflow Failed*\n"
        f"Error: {error}\n"
        f"Check logs for details."
    )


def fmt_skip(phase: str, reason: str) -> str:
    return f"⏭️ *{phase.capitalize()} Skipped* — {reason}"
