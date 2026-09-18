"""Weather categorization.

Two strategies coexist:
- ``categorize_by_keywords`` — deterministic keyword matching used to build the
  seed set from the general-purpose meme dataset (reliable, no false positives).
- ``categorize`` — zero-shot embedding categorization used for open text, for
  example user-submitted memes that arrive without an explicit category.
"""

from __future__ import annotations

import numpy as np

from .embedding import build_embedder

CATEGORIES = ["hot", "cold", "rain", "snow", "wind", "comfort"]

# Anchor texts describe each weather category for the embedding similarity search.
ANCHORS = {
    "hot": "жара солнце пекло зной лето пляж духота",
    "cold": "холод мороз замерз зима лед стужа",
    "rain": "дождь ливень зонт лужа мокро сыро",
    "snow": "снег снегопад сугроб метель зима",
    "wind": "ветер ураган шторм вихрь сдувает",
    "comfort": "хорошая погода ясно солнце тепло комфорт",
}

# Keyword stems for the deterministic seed filter. Chosen to be specific enough to
# avoid false positives present in the source dataset (e.g. "солнцезащитные очки").
CATEGORY_KEYWORDS = {
    "hot": ["жарк", "жара", "жару", "жары", "жарой", "зной", "пекло", "духот"],
    "cold": ["мороз", "замерз", "стуж", "холод", "прохлад"],
    "rain": ["дожд", "ливн", "зонт", "лужа", "лужи", "мокр", "промок"],
    "snow": ["снег", "снеж", "сугроб", "метел"],
    "wind": ["ветер", "ветря", "ветро", "ураган", "шторм", "вихрь"],
    "comfort": ["погод", "тепл", "ясно", "ясная"],
}

# Homonym colliders that must not trigger their category (e.g. "ветеринар" contains "ветер").
CATEGORY_EXCLUSIONS = {
    "rain": ["дожда", "дождусь", "дождешься", "подожд", "лужайк", "лужок"],
    "wind": ["ветеринар", "ветеран"],
    "comfort": ["объясн", "поясн", "разъясн", "выясн"],
}


def categorize_by_keywords(text: str) -> str | None:
    """Return the category with the most keyword matches, or None if none match."""
    low = text.lower()
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(exclusion in low for exclusion in CATEGORY_EXCLUSIONS.get(category, [])):
            continue
        scores[category] = sum(1 for keyword in keywords if keyword in low)

    if not scores:
        return None
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


_cached_embedder = None


def categorize(descriptions: list[str]) -> list[str]:
    """Zero-shot categorization via embeddings (used for user-submitted memes).

    The embedder is loaded once and cached: initializing fastembed on every request
    would reload the model from disk.
    """
    global _cached_embedder
    anchors = [ANCHORS[c] for c in CATEGORIES]
    if _cached_embedder is None:
        _cached_embedder = build_embedder(descriptions + anchors)
    embedder = _cached_embedder

    desc_vectors = embedder.encode(descriptions)
    anchor_vectors = embedder.encode(anchors)

    similarities = desc_vectors @ anchor_vectors.T
    best = np.argmax(similarities, axis=1)
    return [CATEGORIES[i] for i in best]
