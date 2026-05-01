"""Twilio WhatsApp + SMS sender. Tool surface for the agent."""

from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

TWILIO_TIMEOUT = httpx.Timeout(15.0, connect=5.0)


class NotificationMCPServer:
    @property
    def _account_sid(self) -> str:
        return settings.twilio_account_sid

    def _auth(self) -> tuple:
        return (settings.twilio_account_sid, settings.twilio_auth_token)

    def _url(self) -> str:
        return f"https://api.twilio.com/2010-04-01/Accounts/{self._account_sid}/Messages.json"

    async def _post(self, payload: Dict[str, str]) -> Dict[str, Any]:
        settings.require("twilio")
        async with httpx.AsyncClient(timeout=TWILIO_TIMEOUT) as client:
            response = await client.post(self._url(), data=payload, auth=self._auth())
            if response.status_code >= 400:
                logger.error("twilio %d: %s", response.status_code, response.text[:500])
                response.raise_for_status()
            return response.json()

    async def send_whatsapp(self, message: str) -> Dict[str, Any]:
        try:
            result = await self._post({
                "From": f"whatsapp:{settings.twilio_from_number}",
                "To": f"whatsapp:{settings.twilio_to_number}",
                "Body": message,
            })
            return {"status": "sent", "channel": "whatsapp", "message_sid": result.get("sid")}
        except Exception as exc:  # noqa: BLE001
            return {"status": "failed", "channel": "whatsapp", "error": str(exc)}

    async def send_sms(self, message: str) -> Dict[str, Any]:
        try:
            result = await self._post({
                "From": settings.twilio_from_number,
                "To": settings.twilio_to_number,
                "Body": message,
            })
            return {"status": "sent", "channel": "sms", "message_sid": result.get("sid")}
        except Exception as exc:  # noqa: BLE001
            return {"status": "failed", "channel": "sms", "error": str(exc)}

    async def send_alert(self, message: str) -> Dict[str, Any]:
        """Critical alerts always go via SMS for highest delivery reliability."""
        try:
            result = await self._post({
                "From": settings.twilio_from_number,
                "To": settings.twilio_to_number,
                "Body": f"\U0001F6A8 CRITICAL: {message}",
            })
            return {"status": "alert_sent", "channel": "sms_alert", "message_sid": result.get("sid")}
        except Exception as exc:  # noqa: BLE001
            return {"status": "alert_failed", "error": str(exc)}


notif_server = NotificationMCPServer()
