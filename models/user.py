from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime, timezone


class User:
    def __init__(self, user_doc):
        self._id = user_doc["_id"]
        self.email = user_doc["email"]
        self.password_hash = user_doc["password_hash"]
        self.display_name = user_doc.get("display_name", "")
        self.quest_domain = user_doc.get("quest_domain", "general")
        self.daily_target = user_doc.get("daily_target", 3)
        self.weekly_target = user_doc.get("weekly_target", 15)
        self.total_nos = user_doc.get("total_nos", 0)
        self.total_attempts = user_doc.get("total_attempts", 0)
        self.total_wins = user_doc.get("total_wins", 0)
        self.current_streak = user_doc.get("current_streak", 0)
        self.longest_streak = user_doc.get("longest_streak", 0)
        self.last_attempt_date = user_doc.get("last_attempt_date")
        self.completed_at = user_doc.get("completed_at")

    def get_id(self):
        return str(self._id)

    @property
    def has_completed(self):
        return self.total_nos >= 1000

    def to_dict(self):
        return {
            "id": str(self._id),
            "email": self.email,
            "display_name": self.display_name,
            "quest_domain": self.quest_domain,
            "daily_target": self.daily_target,
            "weekly_target": self.weekly_target,
            "total_nos": self.total_nos,
            "total_attempts": self.total_attempts,
            "total_wins": self.total_wins,
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "has_completed": self.has_completed,
            "completed_at": self.completed_at.isoformat() if isinstance(self.completed_at, datetime) else self.completed_at,
        }


def create_user(db, email, password, display_name, quest_domain="general"):
    user_doc = {
        "email": email.lower().strip(),
        "password_hash": generate_password_hash(password),
        "display_name": display_name.strip(),
        "quest_domain": quest_domain,
        "daily_target": 3,
        "weekly_target": 15,
        "total_nos": 0,
        "total_attempts": 0,
        "total_wins": 0,
        "current_streak": 0,
        "longest_streak": 0,
        "last_attempt_date": None,
        "completed_at": None,
        "created_at": datetime.now(timezone.utc),
    }
    result = db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    return User(user_doc)


def find_user_by_email(db, email):
    doc = db.users.find_one({"email": email.lower().strip()})
    if doc:
        return User(doc)
    return None


def find_user_by_id(db, user_id):
    doc = db.users.find_one({"_id": ObjectId(user_id)})
    if doc:
        return User(doc)
    return None


def verify_password(user, password):
    return check_password_hash(user.password_hash, password)


def update_user_settings(db, user_id, display_name, quest_domain, daily_target, weekly_target):
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "display_name": display_name.strip(),
            "quest_domain": quest_domain,
            "daily_target": daily_target,
            "weekly_target": weekly_target,
        }},
    )


def ensure_indexes(db):
    db.users.create_index("email", unique=True)
    db.attempts.create_index([("user_id", 1), ("date", -1)])
    db.attempts.create_index([("user_id", 1), ("created_at", -1)])
    db.completed_combos.create_index([("user_id", 1), ("combo_id", 1)], unique=True)
