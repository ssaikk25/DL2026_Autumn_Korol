"""Bundled starter memes for an empty database.

A fresh clone has no .db file (databases are not committed), so until
python -m app.ml.pipeline is run the weather endpoint would return
meme: null. These few committed images are inserted on startup when the
database contains no memes, so the app works out of the box. Running the
pipeline afterwards replaces them with the full dataset selection.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .db import SessionLocal
from .models import Meme, MemeCategory, MemeStats

logger = logging.getLogger(__name__)

# Committed to git (see the .gitignore exceptions): starter_<category>_<n>.jpg
STARTER_MEMES_DIR = Path(__file__).resolve().parents[1] / "static" / "memes"


def seed_starter_memes_if_empty() -> int:
    """Insert starter memes into an empty database; return the number added."""
    with SessionLocal() as db:
        if db.query(Meme).count() > 0:
            return 0

        added = 0
        for path in sorted(STARTER_MEMES_DIR.glob("starter_*.jpg")):
            # File name format: starter_<category>_<n>.jpg
            parts = path.stem.split("_")
            if len(parts) != 3:
                continue
            try:
                category = MemeCategory(parts[1])
            except ValueError:
                continue
            meme = Meme(
                image_path=f"/static/memes/{path.name}",
                description="",
                category=category,
                source="starter",
            )
            meme.stats = MemeStats(alpha=1.0, beta=1.0)
            db.add(meme)
            added += 1
        db.commit()

    if added:
        logger.info("Seeded %d starter memes into the empty database", added)
    else:
        logger.warning(
            "Database is empty and no starter memes were found; "
            "run 'python -m app.ml.pipeline' to fill it"
        )
    return added
