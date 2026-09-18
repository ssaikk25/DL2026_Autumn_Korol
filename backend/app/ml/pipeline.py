"""End-to-end ML pipeline: select weather-relevant memes and seed the database."""

from __future__ import annotations

import argparse
from collections import Counter

from ..db import SessionLocal
from ..models import Feedback, Meme, MemeCategory, MemeStats
from .categorize import categorize_by_keywords
from .fetch_memes import iter_rows, load_table, save_image


def run(limit: int | None = None, offset: int = 0) -> dict:
    """Select weather-relevant memes by keywords, save images and seed the database."""
    table = load_table()
    selected: list[tuple[str, str, str]] = []  # (image_path, description, category)

    for index, raw, description in iter_rows(table, offset=offset, limit=limit):
        category = categorize_by_keywords(description)
        if category is None or not raw:
            continue
        image_path = save_image(raw, index)
        selected.append((image_path, description, category))

    with SessionLocal() as db:
        # Reset child tables first: bulk delete() does not trigger ORM cascades.
        db.query(Feedback).delete()
        db.query(MemeStats).delete()
        db.query(Meme).delete()
        for image_path, description, category in selected:
            meme = Meme(
                image_path=image_path,
                description=description,
                category=MemeCategory(category),
                source="rumeme-desc",
                is_active=True,
            )
            meme.stats = MemeStats(alpha=1.0, beta=1.0)
            db.add(meme)
        db.commit()

    distribution = dict(Counter(c for _, _, c in selected))
    return {"selected": len(selected), "inserted": len(selected), "distribution": distribution}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Select weather memes and seed the database")
    parser.add_argument("--limit", type=int, default=None, help="max rows to scan")
    parser.add_argument("--offset", type=int, default=0, help="starting row in the dataset")
    args = parser.parse_args()

    summary = run(limit=args.limit, offset=args.offset)
    print(summary)
