"""Tests for the deterministic weather categorization logic."""

from app.ml.categorize import categorize_by_keywords
from app.services.categories import describe_code, forecast_category, weather_to_category


def test_weather_to_category_snow():
    assert weather_to_category(71, -5.0, 3.0) == "snow"
    assert weather_to_category(75, 0.0, 5.0) == "snow"


def test_weather_to_category_rain_and_thunder():
    assert weather_to_category(61, 12.0, 4.0) == "rain"
    assert weather_to_category(95, 25.0, 6.0) == "rain"


def test_weather_to_category_temperature_priority():
    assert weather_to_category(0, 32.0, 3.0) == "hot"
    assert weather_to_category(0, -10.0, 3.0) == "cold"
    assert weather_to_category(0, 18.0, 20.0) == "wind"
    assert weather_to_category(0, 18.0, 3.0) == "hot"  # mild weather maps to sunny/warm


def test_weather_to_category_snow_beats_temperature():
    # Snow code wins even when the temperature is above zero.
    assert weather_to_category(71, 1.0, 2.0) == "snow"


def test_describe_code():
    assert describe_code(0) == "Ясно"
    assert describe_code(999) == "Неизвестно"


def test_forecast_category():
    assert forecast_category(71, -6.0, -2.0) == "snow"
    # Average 30 > HOT_TEMP (27).
    assert forecast_category(0, 28.0, 32.0) == "hot"


def test_categorize_by_keywords_basic():
    assert categorize_by_keywords("на улице идёт дождь") == "rain"
    assert categorize_by_keywords("выпал снег и сугробы") == "snow"
    assert categorize_by_keywords("обычный мем про жизнь") is None


def test_categorize_by_keywords_exclusions():
    # "ветеринар" contains "ветер" but must not be categorized as wind.
    assert categorize_by_keywords("сегодня первый день работы ветеринаром") is None
    # "дождусь" contains "дожд" but means "wait", not rain.
    assert categorize_by_keywords("я тебя дождусь") is None
