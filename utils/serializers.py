from bson import ObjectId
from datetime import datetime


def serialize_attempt(attempt):
    if not attempt:
        return None
    return {
        "id": str(attempt["_id"]),
        "date": attempt.get("date", ""),
        "created_at": attempt["created_at"].isoformat() if isinstance(attempt.get("created_at"), datetime) else str(attempt.get("created_at", "")),
        "description": attempt.get("description", ""),
        "nos_count": attempt.get("nos_count", 0),
        "quest_domain": attempt.get("quest_domain", ""),
        "reflection_asked": attempt.get("reflection_asked", ""),
        "reflection_learned": attempt.get("reflection_learned", ""),
        "reflection_control": attempt.get("reflection_control", ""),
        "unexpected_win": attempt.get("unexpected_win", False),
        "win_description": attempt.get("win_description", ""),
    }


def serialize_attempts_list(attempts):
    return [serialize_attempt(a) for a in attempts]
