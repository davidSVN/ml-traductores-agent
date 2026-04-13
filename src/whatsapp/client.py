import logging

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

GRAPH_API_BASE = "https://graph.facebook.com"


class WhatsAppClient:
    def __init__(self) -> None:
        self._token = settings.meta_access_token
        self._phone_id = settings.meta_phone_number_id
        self._api_version = settings.meta_api_version
        self._base_url = f"{GRAPH_API_BASE}/{self._api_version}/{self._phone_id}/messages"
        self._client = httpx.AsyncClient(timeout=30.0)

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def send_text(self, to: str, text: str) -> None:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        await self._post(payload)

    async def send_document(
        self,
        to: str,
        document_url: str,
        filename: str,
        caption: str = "",
    ) -> None:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename,
                "caption": caption,
            },
        }
        await self._post(payload)

    async def _post(self, payload: dict) -> None:
        try:
            logger.debug(f"WhatsApp POST → {self._base_url} | payload={payload}")
            response = await self._client.post(
                self._base_url,
                headers=self._headers,
                json=payload,
            )
            logger.debug(f"WhatsApp response: {response.status_code} {response.text}")
            if response.status_code >= 400:
                logger.error(f"WhatsApp API error {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
