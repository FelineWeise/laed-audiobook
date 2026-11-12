from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_gateway_url: str = Field(
        default="https://litellm.laed.eu/v1",
        validation_alias="LLM_GATEWAY_URL",
    )
    llm_gateway_key: str = Field(default="", validation_alias="LLM_GATEWAY_KEY")
    # Optional Caddy basicauth in front of litellm.laed.eu (Mac clients).
    caddy_user: str = Field(default="", validation_alias="CADDY_USER")
    caddy_pass: str = Field(default="", validation_alias="CADDY_PASS")
    chat_model: str = Field(
        default="scaleway/mistral-small",
        validation_alias="AUDIOBOOK_CHAT_MODEL",
    )
    tts_model: str = Field(
        default="tts/kokoro",
        validation_alias="AUDIOBOOK_TTS_MODEL",
    )
    tts_voice: str = Field(default="af_heart", validation_alias="AUDIOBOOK_TTS_VOICE")
    tts_speed: float = Field(default=1.0, validation_alias="AUDIOBOOK_TTS_SPEED")
    chunk_max_words: int = Field(default=220, validation_alias="AUDIOBOOK_CHUNK_WORDS")
    output_dir: Path = Field(
        default_factory=lambda: Path.home() / "Desktop",
        validation_alias="AUDIOBOOK_OUTPUT_DIR",
    )
    request_timeout_s: float = Field(default=180.0, validation_alias="AUDIOBOOK_TIMEOUT")

    def require_key(self) -> None:
        if not self.llm_gateway_key.strip():
            raise ValueError(
                "LLM_GATEWAY_KEY is empty. Set a budgeted consumer key from llm-gateway."
            )
