from bson import ObjectId
from datetime import datetime, date, timedelta, timezone


def log_attempt(db, user_id, description, nos_count, quest_domain, reflection_asked="",
                reflection_learned="", reflection_control=""):
    today_str = date.today().isoformat()
    now = datetime.now(timezone.utc)

    attempt_doc = {
        "user_id": ObjectId(user_id),
        "date": today_str,
        "created_at": now,
        "description": description.strip(),
        "nos_count": nos_count,
        "quest_domain": quest_domain,
        "reflection_asked": reflection_asked.strip(),
        "reflection_learned": reflection_learned.strip(),
        "reflection_control": reflection_control.strip(),
        "unexpected_win": False,
        "win_description": "",
    }

    result = db.attempts.insert_one(attempt_doc)
    attempt_doc["_id"] = result.inserted_id

    # Update user counters and streak
    user_doc = db.users.find_one({"_id": ObjectId(user_id)})
    last_attempt_date = user_doc.get("last_attempt_date")
    current_streak = user_doc.get("current_streak", 0)
    longest_streak = user_doc.get("longest_streak", 0)

    yesterday_str = (date.today() - timedelta(days=1)).isoformat()

    if last_attempt_date == today_str:
        # Same day — no streak change
        new_streak = current_streak
    elif last_attempt_date == yesterday_str:
        # Consecutive day — increment streak
        new_streak = current_streak + 1
    else:
        # Gap or first attempt — reset to 1
        new_streak = 1

    new_longest = max(longest_streak, new_streak)
    new_total_nos = user_doc.get("total_nos", 0) + nos_count

    update = {
        "$inc": {"total_attempts": 1, "total_nos": nos_count},
        "$set": {
            "last_attempt_date": today_str,
            "current_streak": new_streak,
            "longest_streak": new_longest,
        },
    }

    # Check if just crossed 1000
    if new_total_nos >= 1000 and not user_doc.get("completed_at"):
        update["$set"]["completed_at"] = now

    db.users.update_one({"_id": ObjectId(user_id)}, update)

    return attempt_doc


def toggle_win(db, attempt_id, user_id, win_description=""):
    attempt = db.attempts.find_one({"_id": ObjectId(attempt_id), "user_id": ObjectId(user_id)})
    if not attempt:
        return None

    new_win_state = not attempt.get("unexpected_win", False)
    db.attempts.update_one(
        {"_id": ObjectId(attempt_id)},
        {"$set": {
            "unexpected_win": new_win_state,
            "win_description": win_description.strip() if new_win_state else "",
        }},
    )

    # Update user win counter
    inc_val = 1 if new_win_state else -1
    db.users.update_one({"_id": ObjectId(user_id)}, {"$inc": {"total_wins": inc_val}})

    return new_win_state


def update_reflection(db, attempt_id, user_id, reflection_asked, reflection_learned, reflection_control):
    result = db.attempts.update_one(
        {"_id": ObjectId(attempt_id), "user_id": ObjectId(user_id)},
        {"$set": {
            "reflection_asked": reflection_asked.strip(),
            "reflection_learned": reflection_learned.strip(),
            "reflection_control": reflection_control.strip(),
        }},
    )
    return result.modified_count > 0


def get_attempt(db, attempt_id, user_id):
    return db.attempts.find_one({"_id": ObjectId(attempt_id), "user_id": ObjectId(user_id)})


def get_attempts_paginated(db, user_id, page=1, per_page=20):
    skip = (page - 1) * per_page
    cursor = db.attempts.find({"user_id": ObjectId(user_id)}).sort("created_at", -1).skip(skip).limit(per_page)
    attempts = list(cursor)
    total = db.attempts.count_documents({"user_id": ObjectId(user_id)})
    return attempts, total


def get_recent_attempts(db, user_id, limit=5):
    cursor = db.attempts.find({"user_id": ObjectId(user_id)}).sort("created_at", -1).limit(limit)
    return list(cursor)


def get_daily_stats(db, user_id):
    today_str = date.today().isoformat()
    pipeline = [
        {"$match": {"user_id": ObjectId(user_id), "date": today_str}},
        {"$group": {
            "_id": None,
            "count": {"$sum": 1},
            "nos": {"$sum": "$nos_count"},
        }},
    ]
    result = list(db.attempts.aggregate(pipeline))
    if result:
        return {"count": result[0]["count"], "nos": result[0]["nos"]}
    return {"count": 0, "nos": 0}


def get_weekly_stats(db, user_id):
    today = date.today()
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    pipeline = [
        {"$match": {"user_id": ObjectId(user_id), "date": {"$gte": week_start}}},
        {"$group": {
            "_id": None,
            "count": {"$sum": 1},
            "nos": {"$sum": "$nos_count"},
        }},
    ]
    result = list(db.attempts.aggregate(pipeline))
    if result:
        return {"count": result[0]["count"], "nos": result[0]["nos"]}
    return {"count": 0, "nos": 0}


def get_endgame_stats(db, user_id):
    pipeline = [
        {"$match": {"user_id": ObjectId(user_id)}},
        {"$group": {
            "_id": "$date",
            "nos": {"$sum": "$nos_count"},
            "attempts": {"$sum": 1},
            "wins": {"$sum": {"$cond": ["$unexpected_win", 1, 0]}},
        }},
        {"$sort": {"_id": 1}},
    ]
    daily_data = list(db.attempts.aggregate(pipeline))

    domain_pipeline = [
        {"$match": {"user_id": ObjectId(user_id)}},
        {"$group": {
            "_id": "$quest_domain",
            "nos": {"$sum": "$nos_count"},
            "attempts": {"$sum": 1},
        }},
        {"$sort": {"nos": -1}},
    ]
    domain_data = list(db.attempts.aggregate(domain_pipeline))

    return {"daily": daily_data, "domains": domain_data}
