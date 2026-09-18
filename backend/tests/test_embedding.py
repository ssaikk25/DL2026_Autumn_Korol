"""Tests for the NumPy TF-IDF embedding fallback."""

import numpy as np

from app.ml.embedding import TfidfEmbedder


def test_tfidf_vectors_are_normalized():
    embedder = TfidfEmbedder().fit(["дождь зонт лужи", "снег мороз зима"])
    vectors = embedder.encode(["дождь и зонт", "снег и мороз"])

    assert vectors.shape == (2, len(embedder._vocab))
    norms = np.linalg.norm(vectors, axis=1)
    assert np.allclose(norms, 1.0)


def test_tfidf_cosine_ranks_similar_texts_higher():
    embedder = TfidfEmbedder().fit(
        ["дождь зонт лужи мокро", "снег мороз зима холод", "жара солнце пекло"]
    )

    rain_a = embedder.encode(["дождь зонт"])[0]
    rain_b = embedder.encode(["дождь зонт лужи"])[0]
    snow = embedder.encode(["снег мороз"])[0]

    # Rain texts are closer to each other than to the snow text.
    assert float(rain_a @ rain_b) > float(rain_a @ snow)
