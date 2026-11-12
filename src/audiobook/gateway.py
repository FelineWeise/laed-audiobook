from __future__ import annotations

import httpx

from audiobook.config import Settings


class GatewayClient:
    def __init__(self, settings: Settings) -> None:
        settings.require_key()
        self._settings = settings
        auth = None
        if settings.caddy_user and settings.caddy_pass:
            auth = httpx.BasicAuth(settings.caddy_user, settings.caddy_pass)
        self._client = httpx.Client(
            base_url=settings.llm_gateway_url.rstrip("/"),
            headers={"Authorization": f"Bearer {settings.llm_gateway_key}"},
            timeout=settings.request_timeout_s,
            auth=auth,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> GatewayClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def chat_completion(self, *, model: str, user_prompt: str) -> str:
        response = self._client.post(
            "/chat/completions",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You write spoken scripts for text-to-speech. "
                            "Return only the script body."
                        ),
                    },
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
            },
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("Chat completion returned no choices.")
        content = choices[0].get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Chat completion returned empty content.")
        return content.strip()

    def speech(self, *, model: str, text: str, voice: str, speed: float) -> bytes:
        response = self._client.post(
            "/audio/speech",
            json={
                "model": model,
                "input": text,
                "voice": voice,
                "speed": speed,
                "response_format": "mp3",
            },
        )
        response.raise_for_status()
        audio = response.content
        if not audio:
            raise RuntimeError("TTS returned empty audio.")
        return audio
