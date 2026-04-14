import logging
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from src.config import settings
from src.utils.embeddings import EMBEDDING_DIMENSION, generate_embedding, build_profile_text

logger = logging.getLogger("suhird.qdrant")

COLLECTION_NAME = "suhird_profiles"

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        _ensure_collection()
    return _client


def _ensure_collection() -> None:
    client = _client
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIMENSION, distance=Distance.COSINE),
        )
        logger.info("Created Qdrant collection %s", COLLECTION_NAME)


async def upsert_profile(user_id: UUID, user_data: dict) -> None:
    text = build_profile_text(user_data)
    embedding = await generate_embedding(text)
    client = get_client()

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=str(user_id),
                vector=embedding,
                payload={
                    "user_id": str(user_id),
                    "gender": user_data.get("gender", ""),
                    "age": user_data.get("age", 0),
                    "location": user_data.get("location", ""),
                },
            )
        ],
    )
    logger.info("Upserted profile vector for user %s", user_id)


async def search_similar(
    user_id: UUID,
    user_data: dict,
    limit: int = 20,
    exclude_ids: list[str] | None = None,
) -> list[dict]:
    text = build_profile_text(user_data)
    embedding = await generate_embedding(text)
    client = get_client()

    must_not = [FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))]
    if exclude_ids:
        for eid in exclude_ids:
            must_not.append(FieldCondition(key="user_id", match=MatchValue(value=eid)))

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=embedding,
        limit=limit,
        query_filter=Filter(must_not=must_not),
    )

    return [
        {
            "user_id": hit.payload["user_id"],
            "score": hit.score,
        }
        for hit in results
    ]


async def delete_profile(user_id: UUID) -> None:
    client = get_client()
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=[str(user_id)],
    )
    logger.info("Deleted profile vector for user %s", user_id)
