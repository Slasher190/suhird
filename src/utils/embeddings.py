import logging

import httpx

from src.config import settings

logger = logging.getLogger("suhird.embeddings")

EMBEDDING_DIMENSION = 768


async def generate_embedding(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.ollama_host}/api/embeddings",
            json={"model": settings.ollama_model, "prompt": text},
        )
        response.raise_for_status()
        data = response.json()
        return data["embedding"]


def build_profile_text(user_data: dict) -> str:
    """Concatenate profile fields into a single string for embedding."""
    parts = []

    if user_data.get("name"):
        parts.append(f"Name: {user_data['name']}")
    if user_data.get("age"):
        parts.append(f"Age: {user_data['age']}")
    if user_data.get("gender"):
        parts.append(f"Gender: {user_data['gender']}")
    if user_data.get("location"):
        parts.append(f"Location: {user_data['location']}")

    bio = user_data.get("bio_prompts", {})
    if bio:
        for prompt_key, answer in bio.items():
            parts.append(f"{prompt_key}: {answer}")

    interests = user_data.get("interests", [])
    if interests:
        parts.append(f"Interests: {', '.join(interests)}")

    lifestyle = user_data.get("lifestyle", {})
    if lifestyle:
        for key, val in lifestyle.items():
            parts.append(f"{key}: {val}")

    values_data = user_data.get("values_data", {})
    if values_data:
        for key, val in values_data.items():
            parts.append(f"{key}: {val}")

    if user_data.get("relationship_type"):
        parts.append(f"Looking for: {user_data['relationship_type']}")

    return ". ".join(parts)
