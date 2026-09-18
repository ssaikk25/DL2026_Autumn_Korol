"""Thompson sampling recommender over memes within a weather category."""

from __future__ import annotations

import json
import random

from sqlalchemy.orm import joinedload

from ..db import SessionLocal
from ..models import Feedback, Meme, MemeCategory, MemeStats, Vote


def recommend_meme(category: str) -> Meme | None:
    """Pick the best meme for `category` by sampling each candidate's Beta(alpha, beta).

    Thompson sampling balances exploration and exploitation: memes with a high
    observed like rate are shown more often, while under-tested memes still get
    occasional exposure.
    """
    with SessionLocal() as db:
        memes = (
            db.query(Meme)
            .options(joinedload(Meme.stats))
            .filter(Meme.category == MemeCategory(category), Meme.is_active.is_(True))
            .all()
        )
        if not memes:
            return None

        best: Meme | None = None
        best_score = -1.0
        for meme in memes:
            if meme.stats is None:
                meme.stats = MemeStats(meme_id=meme.id, alpha=1.0, beta=1.0)
                db.add(meme.stats)
            score = random.betavariate(max(meme.stats.alpha, 1e-6), max(meme.stats.beta, 1e-6))
            if score > best_score:
                best_score = score
                best = meme

        if best is not None and best.stats is not None:
            best.stats.impressions += 1
        db.commit()
        return best


def record_feedback(
    meme_id: int, vote: str, category: str, weather_context: dict | None = None
) -> dict | None:
    """Apply a vote to a meme's Beta parameters and store the feedback row."""
    with SessionLocal() as db:
        if db.get(Meme, meme_id) is None:
            return None

        stats = db.get(MemeStats, meme_id)
        if stats is None:
            stats = MemeStats(meme_id=meme_id, alpha=1.0, beta=1.0)
            db.add(stats)

        if vote == "up":
            stats.likes += 1
            stats.alpha += 1.0
        else:
            stats.dislikes += 1
            stats.beta += 1.0

        db.add(
            Feedback(
                meme_id=meme_id,
                vote=Vote(vote),
                category=category,
                weather_context=json.dumps(weather_context or {}, ensure_ascii=False),
            )
        )
        db.commit()
        return {
            "meme_id": meme_id,
            "likes": stats.likes,
            "dislikes": stats.dislikes,
            "alpha": round(stats.alpha, 4),
            "beta": round(stats.beta, 4),
        }


def top_memes(category: str | None = None, limit: int = 10) -> list[Meme]:
    """Return the highest-rated memes, measured by the mean of their Beta distribution."""
    with SessionLocal() as db:
        query = db.query(Meme).options(joinedload(Meme.stats)).filter(Meme.is_active.is_(True))
        if category:
            query = query.filter(Meme.category == MemeCategory(category))
        memes = query.all()

        def mean_score(meme: Meme) -> float:
            if meme.stats is None:
                return 0.5
            return meme.stats.alpha / (meme.stats.alpha + meme.stats.beta)

        memes.sort(key=mean_score, reverse=True)
        return memes[:limit]
