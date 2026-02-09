from flask import Blueprint, request, jsonify, current_app
from utils.jwt_auth import token_required, get_daily_quote
from utils.serializers import serialize_attempts_list
from models.attempt import get_recent_attempts, get_daily_stats, get_weekly_stats
from models.user import update_user_settings, find_user_by_id

api_user_bp = Blueprint("api_user", __name__, url_prefix="/api/me")


@api_user_bp.route("", methods=["GET"])
@token_required
def me():
    user = request.current_user
    db = current_app.db

    daily = get_daily_stats(db, user.get_id())
    weekly = get_weekly_stats(db, user.get_id())
    recent = get_recent_attempts(db, user.get_id())
    quote = get_daily_quote(user.get_id())

    return jsonify({"ok": True, "data": {
        "user": user.to_dict(),
        "daily_quote": quote,
        "daily": daily,
        "weekly": weekly,
        "recent": serialize_attempts_list(recent),
    }})


@api_user_bp.route("/settings", methods=["PUT"])
@token_required
def settings():
    user = request.current_user
    data = request.get_json(silent=True) or {}

    display_name = data.get("display_name", "").strip()
    quest_domain = data.get("quest_domain", user.quest_domain)
    daily_target = data.get("daily_target", user.daily_target)
    weekly_target = data.get("weekly_target", user.weekly_target)

    if not display_name:
        return jsonify({"ok": False, "error": "Display name is required."}), 400

    try:
        daily_target = max(1, min(50, int(daily_target)))
        weekly_target = max(1, min(200, int(weekly_target)))
    except (ValueError, TypeError):
        daily_target = 3
        weekly_target = 15

    db = current_app.db
    update_user_settings(db, user.get_id(), display_name, quest_domain, daily_target, weekly_target)

    updated_user = find_user_by_id(db, user.get_id())
    return jsonify({"ok": True, "data": {"user": updated_user.to_dict()}})
