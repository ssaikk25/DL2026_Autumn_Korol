"""Weather provider abstraction: Open-Meteo implementation, mock fallback and caching."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

from ..config import get_settings
from ..db import SessionLocal
from ..models import WeatherCache
from .categories import describe_code, weather_to_category

settings = get_settings()


@dataclass
class WeatherData:
    temperature: float
    apparent_temperature: float
    humidity: int
    wind_speed: float
    cloud_cover: int
    pressure: float
    weather_code: int
    is_demo: bool = False

    @property
    def description(self) -> str:
        return describe_code(self.weather_code)

    @property
    def category(self) -> str:
        return weather_to_category(self.weather_code, self.temperature, self.wind_speed)

    def to_dict(self) -> dict:
        return {
            "temperature": self.temperature,
            "apparent_temperature": self.apparent_temperature,
            "humidity": self.humidity,
            "wind_speed": self.wind_speed,
            "cloud_cover": self.cloud_cover,
            "pressure": self.pressure,
            "weather_code": self.weather_code,
            "description": self.description,
            "category": self.category,
        }


class WeatherProvider:
    """Interface implemented by every weather source.

    Adding a new provider (e.g. OpenWeatherMap) only requires implementing these
    three methods and swapping the instance in WeatherService.
    """

    async def current(self, latitude: float, longitude: float) -> WeatherData:
        raise NotImplementedError

    async def forecast(self, latitude: float, longitude: float, days: int) -> list[dict]:
        raise NotImplementedError

    async def search_city(self, query: str, limit: int = 5) -> list[dict]:
        raise NotImplementedError


class OpenMeteoProvider(WeatherProvider):
    async def current(self, latitude: float, longitude: float) -> WeatherData:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,apparent_temperature,relative_humidity_2m,"
                "wind_speed_10m,cloud_cover,pressure_msl,weather_code"
            ),
            "timezone": "auto",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.open_meteo_forecast_url, params=params)
            response.raise_for_status()
            payload = response.json()

        current = payload["current"]
        return WeatherData(
            temperature=float(current["temperature_2m"]),
            apparent_temperature=float(current["apparent_temperature"]),
            humidity=int(current["relative_humidity_2m"]),
            wind_speed=float(current["wind_speed_10m"]),
            cloud_cover=int(current["cloud_cover"]),
            pressure=float(current["pressure_msl"]),
            weather_code=int(current["weather_code"]),
        )

    async def forecast(self, latitude: float, longitude: float, days: int) -> list[dict]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "forecast_days": days,
            "timezone": "auto",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.open_meteo_forecast_url, params=params)
            response.raise_for_status()
            payload = response.json()

        daily = payload["daily"]
        return [
            {
                "date": daily["time"][i],
                "weather_code": int(daily["weather_code"][i]),
                "temp_min": float(daily["temperature_2m_min"][i]),
                "temp_max": float(daily["temperature_2m_max"][i]),
            }
            for i in range(len(daily["time"]))
        ]

    async def search_city(self, query: str, limit: int = 5) -> list[dict]:
        params = {"name": query, "count": limit, "language": "ru", "format": "json"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.open_meteo_geocoding_url, params=params)
            response.raise_for_status()
            payload = response.json()

        return [
            {
                "name": item.get("name"),
                "country": item.get("country"),
                "admin1": item.get("admin1"),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "timezone": item.get("timezone"),
            }
            for item in payload.get("results", [])
        ]


class MockProvider(WeatherProvider):
    """Deterministic fallback that produces varied categories from coordinates."""

    _CURRENT_CODES = [0, 1, 2, 3, 45, 61, 63, 71, 73, 80, 95]
    _FORECAST_CODES = [0, 1, 2, 61, 63, 71, 73]

    async def current(self, latitude: float, longitude: float) -> WeatherData:
        seed = int(round(latitude * 1000 + longitude * 1000))
        temperature = round(30.0 - abs(latitude) * 0.5 + (seed % 25) - 12, 1)
        return WeatherData(
            temperature=temperature,
            apparent_temperature=round(temperature - 2.0, 1),
            humidity=40 + (seed % 55),
            wind_speed=round(2.0 + (seed % 18), 1),
            cloud_cover=seed % 101,
            pressure=round(1013.0 + (seed % 20) - 10, 1),
            weather_code=self._CURRENT_CODES[seed % len(self._CURRENT_CODES)],
            is_demo=True,
        )

    async def forecast(self, latitude: float, longitude: float, days: int) -> list[dict]:
        today = datetime.now(timezone.utc).date()
        result = []
        for i in range(days):
            seed = int(round(latitude * 1000 + longitude * 1000)) + i
            code = self._FORECAST_CODES[seed % len(self._FORECAST_CODES)]
            temp_min = round(12.0 - abs(latitude) * 0.3 + (seed % 10) - 5, 1)
            temp_max = round(temp_min + 6.0 + (seed % 5), 1)
            result.append(
                {
                    "date": (today + timedelta(days=i)).isoformat(),
                    "weather_code": code,
                    "temp_min": temp_min,
                    "temp_max": temp_max,
                }
            )
        return result

    async def search_city(self, query: str, limit: int = 5) -> list[dict]:
        # Mock cannot geocode; the service treats geocoding errors as 502 instead.
        raise NotImplementedError


class WeatherService:
    """Cached facade over the provider with automatic mock fallback."""

    def __init__(self) -> None:
        self.provider: WeatherProvider = OpenMeteoProvider()
        self.mock: WeatherProvider = MockProvider()

    async def search_city(self, query: str, limit: int = 5) -> list[dict]:
        return await self.provider.search_city(query, limit)

    async def get_current(self, latitude: float, longitude: float) -> tuple[WeatherData, bool]:
        key = f"weather:{latitude}:{longitude}"
        cached = self._cache_get(key)
        if cached is not None:
            return WeatherData(**cached), False

        try:
            data = await self.provider.current(latitude, longitude)
        except Exception:
            if settings.enable_mock_fallback:
                return await self.mock.current(latitude, longitude), True
            raise
        self._cache_set(key, data)
        return data, False

    async def get_forecast(
        self, latitude: float, longitude: float, days: int
    ) -> tuple[list[dict], bool]:
        try:
            return await self.provider.forecast(latitude, longitude, days), False
        except Exception:
            if settings.enable_mock_fallback:
                return await self.mock.forecast(latitude, longitude, days), True
            raise

    def _cache_get(self, key: str) -> dict | None:
        with SessionLocal() as db:
            row = db.get(WeatherCache, key)
            if row is None:
                return None
            if time.time() - row.fetched_at > settings.weather_cache_ttl_seconds:
                return None
            return json.loads(row.payload)

    def _cache_set(self, key: str, data: WeatherData) -> None:
        payload = json.dumps(
            {
                "temperature": data.temperature,
                "apparent_temperature": data.apparent_temperature,
                "humidity": data.humidity,
                "wind_speed": data.wind_speed,
                "cloud_cover": data.cloud_cover,
                "pressure": data.pressure,
                "weather_code": data.weather_code,
            }
        )
        with SessionLocal() as db:
            row = db.get(WeatherCache, key)
            if row is None:
                db.add(WeatherCache(key=key, payload=payload, fetched_at=time.time()))
            else:
                row.payload = payload
                row.fetched_at = time.time()
            db.commit()
