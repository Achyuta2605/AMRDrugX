import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from app.data.target_knowledge_base import TARGET_KNOWLEDGE_BASE

GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
GEMINI_EMBEDDING_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_EMBEDDING_MODEL}:embedContent"
)

CACHE_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "cache"
    / "target_embeddings.json"
)


def get_gemini_api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY")


def gemini_embeddings_available() -> bool:
    return bool(get_gemini_api_key())


def load_embedding_cache() -> dict[str, Any]:
    if not CACHE_PATH.exists():
        return {}

    with CACHE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_embedding_cache(cache: dict[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with CACHE_PATH.open("w", encoding="utf-8") as file:
        json.dump(cache, file, indent=2)


def embed_text(text: str, task_type: str) -> list[float]:
    api_key = get_gemini_api_key()

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    payload = {
        "model": f"models/{GEMINI_EMBEDDING_MODEL}",
        "taskType": task_type,
        "content": {
            "parts": [
                {
                    "text": text,
                }
            ]
        },
    }

    request = urllib.request.Request(
        GEMINI_EMBEDDING_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Gemini embedding request failed: {exc}") from exc

    parsed = json.loads(response_body)

    if "embedding" in parsed and "values" in parsed["embedding"]:
        return parsed["embedding"]["values"]

    raise RuntimeError("Gemini embedding response did not contain embedding values.")


def get_target_record_embeddings() -> dict[str, list[float]]:
    cache = load_embedding_cache()
    cached_model = cache.get("model")
    cached_records = cache.get("records", {})

    if cached_model != GEMINI_EMBEDDING_MODEL:
        cached_records = {}

    changed = False

    for record in TARGET_KNOWLEDGE_BASE:
        record_id = record["id"]

        if record_id not in cached_records:
            embedding = embed_text(
                text=record["search_text"],
                task_type="RETRIEVAL_DOCUMENT",
            )
            cached_records[record_id] = {
                "embedding": embedding,
                "search_text": record["search_text"],
            }
            changed = True

    if changed:
        save_embedding_cache(
            {
                "model": GEMINI_EMBEDDING_MODEL,
                "records": cached_records,
            }
        )

    return {
        record_id: record_data["embedding"]
        for record_id, record_data in cached_records.items()
    }