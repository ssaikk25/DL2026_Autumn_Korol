"""Current weather and forecast endpoints."""

from fastapi import APIRouter, HTTPException, Query

from ..schemas import (
    CurrentWeather,
    CurrentWeatherResponse,
    ForecastDay,
    ForecastResponse,
)
from ..services.categories import describe_code, forecast_category
from ..services.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["weather"])
service = WeatherService()


async def _resolve_location(city: str | None, lat: float | None, lon: float | None) -> tuple[dict, float, float]:
    """Return (location dict, latitude, longitude) for a city or explicit coordinates."""
    if city is None and (lat is None or lon is None):
        raise HTTPException(status_code=400, detail="Provide either 'city' or both 'lat' and 'lon'")

    if city:
        try:
            results = await service.search_city(city, limit=1)
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Geocoding provider is unavailable") from exc
        if not results:
            raise HTTPException(status_code=404, detail=f"City not found: {city}")
        first = results[0]
        return first, first["latitude"], first["longitude"]

    return {"latitude": lat, "longitude": lon}, lat, lon


@router.get("/current", response_model=CurrentWeatherResponse)
async def current_weather(
    city: str | None = Query(None),
    lat: float | None = Query(None),
    lon: float | None = Query(None),
) -> CurrentWeatherResponse:
    location, latitude, longitude = await _resolve_location(city, lat, lon)
    data, is_demo = await service.get_current(latitude, longitude)
    return CurrentWeatherResponse(
        location=location,
        current=CurrentWeather(**data.to_dict()),
        meme=None,  # wired in the memes/feedback step
        is_demo=is_demo,
    )


@router.get("/forecast", response_model=ForecastResponse)
async def forecast(
    city: str | None = Query(None),
    lat: float | None = Query(None),
    lon: float | None = Query(None),
    days: int = Query(5, ge=1, le=7),
) -> ForecastResponse:
    location, latitude, longitude = await _resolve_location(city, lat, lon)
    days_raw, is_demo = await service.get_forecast(latitude, longitude, days)

    result = []
    for day in days_raw:
        category = forecast_category(day["weather_code"], day["temp_min"], day["temp_max"])
        result.append(
            ForecastDay(
                date=day["date"],
                weather_code=day["weather_code"],
                temp_min=day["temp_min"],
                temp_max=day["temp_max"],
                category=category,
                description=describe_code(day["weather_code"]),
                meme=None,
            )
        )
    return ForecastResponse(location=location, days=result, is_demo=is_demo)
