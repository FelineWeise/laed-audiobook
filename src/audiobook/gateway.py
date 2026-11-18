from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

import httpx

from audiobook.config import Settings

T = TypeVar("T")


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

    def chat_completion(
        self,
        *,
        model: str,
        user_prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        system = system_prompt or (
            "You write spoken scripts for text-to-speech. "
            "Return only the script body."
        )

        def _once() -> str:
            response = self._client.post(
                "/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                },
            )
            self._raise_for_status(response)
            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError("Chat completion returned no choices.")
            content = choices[0].get("message", {}).get("content")
            if not isinstance(content, str) or not content.strip():
                raise RuntimeError("Chat completion returned empty content.")
            return content.strip()

        return self._with_retries(_once)

    def speech(self, *, model: str, text: str, voice: str, speed: float) -> bytes:
        def _once() -> bytes:
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
            self._raise_for_status(response)
            audio = response.content
            if not audio:
                raise RuntimeError("TTS returned empty audio.")
            return audio

        return self._with_retries(_once)

    def _with_retries(self, fn: Callable[[], T]) -> T:
        attempts = max(1, self._settings.max_retries + 1)
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return fn()
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError, RuntimeError) as exc:
                last_error = exc
                if isinstance(exc, httpx.HTTPStatusError):
                    code = exc.response.status_code
                    if code < 500 and code not in {408, 429}:
                        raise
                if attempt >= attempts - 1:
                    break
                delay = self._settings.retry_backoff_s * (2**attempt) + random.uniform(0, 0.25)
                time.sleep(delay)
        assert last_error is not None
        raise last_error

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        response.raise_for_status()
