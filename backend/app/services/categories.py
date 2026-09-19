"""Deterministic mapping from Open-Meteo WMO weather codes to meme categories."""

from __future__ import annotations

WMO_DESCRIPTIONS: dict[int, str] = {
    0: "Ясно",
    1: "Преимущественно ясно",
    2: "Переменная облачность",
    3: "Пасмурно",
    45: "Туман",
    48: "Изморозь",
    51: "Лёгкая морось",
    53: "Морось",
    55: "Сильная морось",
    56: "Ледяная морось",
    57: "Ледяная морось",
    61: "Небольшой дождь",
    63: "Дождь",
    65: "Сильный дождь",
    66: "Ледяной дождь",
    67: "Ледяной дождь",
    71: "Небольшой снег",
    73: "Снег",
    75: "Сильный снег",
    77: "Снежная крупа",
    80: "Ливень",
    81: "Ливень",
    82: "Сильный ливень",
    85: "Снегопад",
    86: "Сильный снегопад",
    95: "Гроза",
    96: "Гроза с градом",
    99: "Гроза с градом",
}

_SNOW_CODES = {71, 73, 75, 77, 85, 86}
_RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}

HOT_TEMP = 27.0
COLD_TEMP = 0.0
WIND_SPEED = 15.0


def describe_code(weather_code: int) -> str:
    """Return a Russian description for a WMO weather code."""
    return WMO_DESCRIPTIONS.get(weather_code, "Неизвестно")


def weather_to_category(weather_code: int, temperature: float, wind_speed: float) -> str:
    """Return the meme category for the given weather conditions.

    Priority: snow > rain > hot > cold > wind. Mild/clear weather falls back to the
    sunny/warm category ("hot"), which also covers sun and summer memes.
    """
    if weather_code in _SNOW_CODES:
        return "snow"
    if weather_code in _RAIN_CODES:
        return "rain"
    if temperature >= HOT_TEMP:
        return "hot"
    if temperature <= COLD_TEMP:
        return "cold"
    if wind_speed >= WIND_SPEED:
        return "wind"
    return "hot"


def forecast_category(weather_code: int, temp_min: float, temp_max: float) -> str:
    """Category for a forecast day (no wind data available at daily granularity)."""
    return weather_to_category(weather_code, (temp_min + temp_max) / 2, wind_speed=0.0)
