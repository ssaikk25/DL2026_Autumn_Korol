"""City search (geocoding) endpoint."""

from fastapi import APIRouter, HTTPException, Query

from ..schemas import GeocodeResponse
from ..services.weather_service import WeatherService

router = APIRouter(tags=["geocode"])
service = WeatherService()


@router.get("/geocode", response_model=GeocodeResponse)
async def geocode(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=10),
) -> GeocodeResponse:
    try:
        results = await service.search_city(q, limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Geocoding provider is unavailable") from exc
    return GeocodeResponse(results=results)
