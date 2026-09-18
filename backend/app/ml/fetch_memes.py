"""Access to the rumeme-desc dataset: download the parquet and iterate rows."""

from __future__ import annotations

import io
from pathlib import Path

import httpx
import pyarrow as pa
import pyarrow.parquet as pq
from PIL import Image

DATASET_URL = (
    "https://huggingface.co/datasets/foldl/rumeme-desc/resolve/main/"
    "data/train-00000-of-00001.parquet"
)

BACKEND_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = BACKEND_DIR / "static" / "memes"
DATA_DIR = Path(__file__).resolve().parent / "data"
PARQUET_PATH = DATA_DIR / "rumeme.parquet"

MAX_IMAGE_SIZE = 640


def load_table() -> pa.Table:
    """Download the parquet once and cache it on disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PARQUET_PATH.exists():
        PARQUET_PATH.write_bytes(httpx.get(DATASET_URL, timeout=300, follow_redirects=True).content)
    return pq.read_table(PARQUET_PATH)


def _image_bytes(table: pa.Table) -> list[bytes]:
    column = table.column("image")
    # Hugging Face Image features are serialized as a struct with a 'bytes' field.
    # `column` is a ChunkedArray, so flatten() yields the child arrays by field order.
    if pa.types.is_struct(column.type):
        names = [field.name for field in column.type]
        if "bytes" not in names:
            raise ValueError(f"image struct has no 'bytes' field: {column.type}")
        return column.flatten()[names.index("bytes")].to_pylist()
    return column.to_pylist()


def iter_rows(table: pa.Table, offset: int = 0, limit: int | None = None):
    """Yield (index, image_bytes, description) rows from the dataset."""
    bytes_list = _image_bytes(table)
    texts = table.column("text").to_pylist()
    upper = min(offset + (limit if limit is not None else table.num_rows), table.num_rows)
    for index in range(offset, upper):
        yield index, bytes_list[index], texts[index]


def save_image(raw: bytes, index: int) -> str:
    """Save a meme image resized for the web and return its public path."""
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE))
    filename = f"meme_{index:04d}.jpg"
    image.save(STATIC_DIR / filename, "JPEG", quality=88)
    return f"/static/memes/{filename}"
