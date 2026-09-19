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

CATEGORIES = ["hot", "cold", "rain", "snow", "wind"]

# Anchor texts describe each weather category for the embedding similarity search.
ANCHORS = {
    "hot": "жара солнце пекло зной лето пляж духота",
    "cold": "холод мороз замерз зима лед стужа",
    "rain": "дождь ливень зонт лужа мокро сыро",
    "snow": "снег снегопад сугроб метель зима",
    "wind": "ветер ураган шторм вихрь сдувает",
}

# Keyword stems for the deterministic seed filter. Chosen to be specific enough to
# avoid false positives present in the source dataset (e.g. "солнцезащитные очки").
CATEGORY_KEYWORDS = {
    "hot": ["жарк", "жара", "жару", "жары", "жарой", "зной", "пекло", "духот", "солнечн", "лето", "летн", "пляж", "тепл", "ясн"],
    "cold": ["мороз", "замерз", "стуж", "холод", "прохлад"],
    "rain": ["дожд", "ливн", "зонт", "лужа", "лужи", "мокр", "промок"],
    "snow": ["снег", "снеж", "сугроб", "метел"],
    "wind": ["ветер", "ветря", "ветро", "ураган", "шторм", "вихрь"],
}

# Homonym colliders that must not trigger their category (e.g. "ветеринар" contains "ветер").
CATEGORY_EXCLUSIONS = {
    "hot": ["объясн", "поясн", "разъясн", "выясн"],  # "ясн" must not match "объяснить"
    "rain": ["дожда", "дождусь", "дождешься", "подожд", "лужайк", "лужок"],
    "wind": ["ветеринар", "ветеран"],
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


def semantic_similarities(descriptions: list[str], categories: list[str]) -> list[float]:
    """Cosine similarity of each description to its category's anchor text.

    Used by the pipeline to keep only memes whose description is semantically close
    to the assigned weather category (filtering out keyword false positives).
    """
    anchors = [ANCHORS[c] for c in CATEGORIES]
    embedder = build_embedder(descriptions + anchors)

    desc_vectors = embedder.encode(descriptions)
    anchor_vectors = embedder.encode(anchors)
    category_index = {c: i for i, c in enumerate(CATEGORIES)}

    return [
        float(desc_vectors[i] @ anchor_vectors[category_index[category]])
        for i, category in enumerate(categories)
    ]
