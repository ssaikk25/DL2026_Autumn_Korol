"""Application settings loaded from environment variables and the .env file."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Weather Mood API"
    version: str = "0.1.0"

    # Database
    database_url: str = "sqlite:///./weather_mood.db"

    # External weather provider (Open-Meteo, no API key required)
    open_meteo_geocoding_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    open_meteo_forecast_url: str = "https://api.open-meteo.com/v1/forecast"

    # Caching and fallback behaviour
    weather_cache_ttl_seconds: int = 600
    enable_mock_fallback: bool = True

    # Optional token for write endpoints
    admin_token: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
