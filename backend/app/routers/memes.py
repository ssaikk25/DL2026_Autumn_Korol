"""Meme listing, creation and feedback endpoints."""

from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, Header, HTTPException, Query, UploadFile

from ..config import get_settings
from ..db import SessionLocal
from ..ml.categorize import categorize
from ..models import Meme, MemeCategory, MemeStats
from ..schemas import FeedbackIn, FeedbackOut, MemeListResponse, MemeOut
from ..services import recommender

router = APIRouter(tags=["memes"])
settings = get_settings()

STATIC_MEMES_DIR = Path(__file__).resolve().parents[2] / "static" / "memes"


def _to_meme_out(meme: Meme) -> MemeOut:
    return MemeOut(id=meme.id, image_url=meme.image_path, category=meme.category.value)


def _resolve_category(category: str | None) -> str | None:
    if category is None:
        return None
    try:
        return MemeCategory(category).value
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category}") from exc


@router.get("/memes", response_model=MemeListResponse)
def list_memes(
    category: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> MemeListResponse:
    category = _resolve_category(category)
    with SessionLocal() as db:
        query = db.query(Meme).filter(Meme.is_active.is_(True))
        if category:
            query = query.filter(Meme.category == MemeCategory(category))
        memes = query.limit(limit).all()
    return MemeListResponse(memes=[_to_meme_out(m) for m in memes])


@router.get("/memes/top", response_model=MemeListResponse)
def top_memes(
    category: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
) -> MemeListResponse:
    category = _resolve_category(category)
    return MemeListResponse(memes=[_to_meme_out(m) for m in recommender.top_memes(category, limit)])


@router.post("/memes", response_model=MemeOut, status_code=201)
async def create_meme(
    image: UploadFile = File(...),
    description: str = Form(""),
    category: str | None = Form(None),
    x_admin_token: str | None = Header(None),
) -> MemeOut:
    if settings.admin_token and x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")

    if category:
        try:
            cat = MemeCategory(category).value
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Unknown category: {category}") from exc
    elif description:
        # Zero-shot categorization via embeddings for user-submitted memes.
        cat = categorize([description])[0]
    else:
        raise HTTPException(status_code=400, detail="Provide either 'category' or 'description'")

    STATIC_MEMES_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(image.filename or "meme.jpg").suffix.lower() or ".jpg"
    filename = f"user_{uuid4().hex}{suffix}"
    with (STATIC_MEMES_DIR / filename).open("wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    with SessionLocal() as db:
        meme = Meme(
            image_path=f"/static/memes/{filename}",
            description=description,
            category=MemeCategory(cat),
            source="user",
        )
        meme.stats = MemeStats(alpha=1.0, beta=1.0)
        db.add(meme)
        db.commit()
        db.refresh(meme)
    return _to_meme_out(meme)


@router.post("/memes/{meme_id}/feedback", response_model=FeedbackOut)
def feedback(meme_id: int, payload: FeedbackIn) -> FeedbackOut:
    result = recommender.record_feedback(
        meme_id, payload.vote, payload.category, payload.weather_context
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Meme not found: {meme_id}")
    return FeedbackOut(**result)
