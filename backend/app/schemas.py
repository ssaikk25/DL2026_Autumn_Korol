"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str


class GeocodeResult(BaseModel):
    name: str
    country: str | None = None
    admin1: str | None = None
    latitude: float
    longitude: float
    timezone: str | None = None


class GeocodeResponse(BaseModel):
    results: list[GeocodeResult]


class CurrentWeather(BaseModel):
    temperature: float
    apparent_temperature: float
    humidity: int
    wind_speed: float
    cloud_cover: int
    pressure: float
    weather_code: int
    description: str
    category: str


class MemeOut(BaseModel):
    id: int
    image_url: str
    category: str


class CurrentWeatherResponse(BaseModel):
    location: dict
    current: CurrentWeather
    meme: MemeOut | None = None
    is_demo: bool = False


class ForecastDay(BaseModel):
    date: str
    weather_code: int
    temp_min: float
    temp_max: float
    category: str
    description: str
    meme: MemeOut | None = None


class ForecastResponse(BaseModel):
    location: dict
    days: list[ForecastDay]
    is_demo: bool = False
