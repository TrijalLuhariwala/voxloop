from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VoxLoop API"
    database_url: str = Field(default="sqlite:///./voxloop.db")
    mistral_api_key_primary: str = Field(default="")
    mistral_api_key_critic: str = Field(default="")
    mistral_model_primary: str = Field(default="mistral-small-latest")
    mistral_model_critic: str = Field(default="mistral-small-latest")
    whisper_model_size: str = Field(default="base")
    whisper_device: str = Field(default="cpu")
    whisper_compute_type: str = Field(default="int8")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
