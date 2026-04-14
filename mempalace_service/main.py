"""
MemPalace Wrapper Service -- thin FastAPI wrapper around mempalace for
preference learning in the Suhird matchmaking pipeline.

Stores like/skip interactions per user and queries learned preference patterns.
Each user gets a wing in the palace. Interactions are stored with target profile
attributes so we can learn what the user gravitates toward.
"""
import json
import logging
import os
from collections import Counter, defaultdict
from pathlib import Path

import chromadb
from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mempalace_service")

DATA_DIR = Path(os.environ.get("MEMPALACE_DATA_DIR", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="MemPalace Preference Service", version="1.0.0")

chroma_client = chromadb.PersistentClient(path=str(DATA_DIR / "chromadb"))


def _get_collection(user_id: str):
    return chroma_client.get_or_create_collection(
        name=f"user_{user_id.replace('-', '_')}",
        metadata={"hnsw:space": "cosine"},
    )


class StoreRequest(BaseModel):
    user_id: str
    target_user_id: str
    action: str  # "like" or "pass"
    target_profile: dict


class QueryRequest(BaseModel):
    user_id: str


class ScoreRequest(BaseModel):
    user_id: str
    candidate_profile: dict


@app.post("/store")
async def store_interaction(req: StoreRequest):
    """Store a like/skip interaction with target profile attributes."""
    collection = _get_collection(req.user_id)

    profile_text = _profile_to_text(req.target_profile)

    collection.add(
        ids=[f"{req.user_id}_{req.target_user_id}"],
        documents=[profile_text],
        metadatas=[{
            "action": req.action,
            "target_user_id": req.target_user_id,
            "age": str(req.target_profile.get("age", "")),
            "gender": req.target_profile.get("gender", ""),
            "location": req.target_profile.get("location", ""),
            "interests": ",".join(req.target_profile.get("interests", [])),
        }],
    )

    # Also persist a summary file for fast querying
    _update_preference_summary(req.user_id, req.action, req.target_profile)

    return {"status": "stored", "user_id": req.user_id, "action": req.action}


@app.post("/query")
async def query_preferences(req: QueryRequest):
    """Return learned preference patterns for a user."""
    summary_path = DATA_DIR / f"summary_{req.user_id}.json"
    if not summary_path.exists():
        return {"user_id": req.user_id, "liked_attributes": {}, "skipped_attributes": {}, "interaction_count": 0}

    summary = json.loads(summary_path.read_text())
    return summary


@app.post("/score")
async def score_candidate(req: ScoreRequest):
    """Score a candidate against user's learned preferences."""
    summary_path = DATA_DIR / f"summary_{req.user_id}.json"
    if not summary_path.exists():
        return {"score": 0.5, "confidence": 0.0}

    summary = json.loads(summary_path.read_text())
    liked = summary.get("liked_attributes", {})
    skipped = summary.get("skipped_attributes", {})
    total = summary.get("interaction_count", 0)

    if total == 0:
        return {"score": 0.5, "confidence": 0.0}

    score = 0.5
    candidate_attrs = _extract_attributes(req.candidate_profile)

    for attr in candidate_attrs:
        if attr in liked:
            score += liked[attr] * 0.05
        if attr in skipped:
            score -= skipped[attr] * 0.05

    score = max(0.0, min(1.0, score))
    confidence = min(1.0, total / 20.0)

    return {"score": score, "confidence": confidence}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mempalace"}


def _profile_to_text(profile: dict) -> str:
    parts = []
    for key in ["name", "age", "gender", "location", "relationship_type"]:
        if profile.get(key):
            parts.append(f"{key}: {profile[key]}")
    for interest in profile.get("interests", []):
        parts.append(f"interest: {interest}")
    bio = profile.get("bio_prompts", {})
    for key, val in bio.items():
        parts.append(f"{key}: {val}")
    lifestyle = profile.get("lifestyle", {})
    for key, val in lifestyle.items():
        parts.append(f"{key}: {val}")
    return ". ".join(parts) if parts else "empty profile"


def _extract_attributes(profile: dict) -> list[str]:
    attrs = []
    if profile.get("gender"):
        attrs.append(f"gender:{profile['gender']}")
    if profile.get("location"):
        attrs.append(f"location:{profile['location']}")
    if profile.get("relationship_type"):
        attrs.append(f"rel:{profile['relationship_type']}")
    for interest in profile.get("interests", []):
        attrs.append(f"interest:{interest}")
    lifestyle = profile.get("lifestyle", {})
    for key, val in lifestyle.items():
        attrs.append(f"{key}:{val}")
    values_data = profile.get("values_data", {})
    for key, val in values_data.items():
        attrs.append(f"{key}:{val}")
    if profile.get("age"):
        decade = (profile["age"] // 10) * 10
        attrs.append(f"age_group:{decade}s")
    return attrs


def _update_preference_summary(user_id: str, action: str, profile: dict) -> None:
    summary_path = DATA_DIR / f"summary_{user_id}.json"

    if summary_path.exists():
        summary = json.loads(summary_path.read_text())
    else:
        summary = {"user_id": user_id, "liked_attributes": {}, "skipped_attributes": {}, "interaction_count": 0}

    attrs = _extract_attributes(profile)
    target = "liked_attributes" if action == "like" else "skipped_attributes"

    for attr in attrs:
        summary[target][attr] = summary[target].get(attr, 0) + 1

    summary["interaction_count"] = summary.get("interaction_count", 0) + 1

    # Normalize weights to 0-1 range
    total = summary["interaction_count"]
    for key in ["liked_attributes", "skipped_attributes"]:
        for attr in summary[key]:
            summary[key][attr] = round(summary[key][attr] / total, 3)

    summary_path.write_text(json.dumps(summary, indent=2))
