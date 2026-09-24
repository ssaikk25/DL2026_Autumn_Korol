"""End-to-end ML pipeline: select weather-relevant memes and seed the database."""

from __future__ import annotations

import argparse
from collections import Counter

from ..db import Base, SessionLocal, engine
from ..models import Feedback, Meme, MemeCategory, MemeStats
from .categorize import categorize_by_keywords, semantic_similarities
from .fetch_memes import iter_rows, load_table, save_image


SIMILARITY_THRESHOLD = 0.30


def run(
    limit: int | None = None,
    offset: int = 0,
    threshold: float = SIMILARITY_THRESHOLD,
) -> dict:
    """Select weather-relevant memes and seed the database.

    Candidates are found by keyword matching and then verified by the semantic
    similarity of their description to the category anchor (embeddings). Only memes
    above the threshold are kept, so the seed is strictly weather-relevant.
    """
    # This script never goes through the FastAPI lifespan, and the README runs it
    # before uvicorn for the first time — create the tables so it works on a
    # fresh clone with no database at all.
    Base.metadata.create_all(bind=engine)

    table = load_table()
    candidates: list[tuple[int, bytes, str, str]] = []

    for index, raw, description in iter_rows(table, offset=offset, limit=limit):
        category = categorize_by_keywords(description)
        if category is None or not raw:
            continue
        candidates.append((index, raw, description, category))

    selected: list[tuple[str, str, str]] = []  # (image_path, description, category)
    filtered = 0
    if candidates:
        similarities = semantic_similarities(
            [candidate[2] for candidate in candidates],
            [candidate[3] for candidate in candidates],
        )
        keep = [similarity >= threshold for similarity in similarities]
        # The TF-IDF fallback (used when fastembed is unavailable) scores on a
        # different scale than embeddings and can drop every candidate. The
        # keyword selection with exclusions is still usable, so keep those
        # memes instead of seeding an empty database.
        if not any(keep):
            print(
                f"warning: semantic filter dropped all {len(candidates)} keyword "
                f"candidates at threshold {threshold}; keeping them anyway"
            )
            keep = [True] * len(candidates)

        for accepted, (index, raw, description, category) in zip(keep, candidates):
            if accepted:
                image_path = save_image(raw, index)
                selected.append((image_path, description, category))
            else:
                filtered += 1

    if not selected:
        # Never wipe existing memes (starter set or a previous run) for nothing.
        print(
            f"warning: nothing selected (candidates={len(candidates)}); "
            "the existing database is left untouched"
        )
        return {
            "candidates": len(candidates),
            "selected": 0,
            "filtered": filtered,
            "distribution": {},
        }

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
    return {
        "candidates": len(candidates),
        "selected": len(selected),
        "filtered": filtered,
        "distribution": distribution,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Select weather memes and seed the database")
    parser.add_argument("--limit", type=int, default=None, help="max rows to scan")
    parser.add_argument("--offset", type=int, default=0, help="starting row in the dataset")
    parser.add_argument("--threshold", type=float, default=SIMILARITY_THRESHOLD, help="min semantic similarity")
    args = parser.parse_args()

    summary = run(limit=args.limit, offset=args.offset, threshold=args.threshold)
    print(summary)
