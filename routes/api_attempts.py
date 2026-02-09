from flask import Blueprint, request, jsonify, current_app
from utils.jwt_auth import token_required
from utils.serializers import serialize_attempt, serialize_attempts_list
from models.attempt import (
    log_attempt, toggle_win, update_reflection,
    get_attempt, get_attempts_paginated,
)

api_attempts_bp = Blueprint("api_attempts", __name__, url_prefix="/api/attempts")


@api_attempts_bp.route("", methods=["POST"])
@token_required
def create():
    user = request.current_user
    data = request.get_json(silent=True) or {}

    description = data.get("description", "").strip()
    nos_count = data.get("nos_count", 1)
    quest_domain = data.get("quest_domain", user.quest_domain)
    reflection_asked = data.get("reflection_asked", "")
    reflection_learned = data.get("reflection_learned", "")
    reflection_control = data.get("reflection_control", "")

    if not description:
        return jsonify({"ok": False, "error": "Please describe what you attempted."}), 400

    try:
        nos_count = max(1, min(100, int(nos_count)))
    except (ValueError, TypeError):
        nos_count = 1

    db = current_app.db
    attempt = log_attempt(
        db, user.get_id(), description, nos_count, quest_domain,
        reflection_asked, reflection_learned, reflection_control,
    )

    return jsonify({"ok": True, "data": {"attempt": serialize_attempt(attempt)}}), 201


@api_attempts_bp.route("", methods=["GET"])
@token_required
def history():
    user = request.current_user
    page = request.args.get("page", 1, type=int)
    page = max(1, page)

    db = current_app.db
    attempts, total = get_attempts_paginated(db, user.get_id(), page)
    total_pages = max(1, (total + 19) // 20)

    return jsonify({"ok": True, "data": {
        "attempts": serialize_attempts_list(attempts),
        "total": total,
        "page": page,
        "total_pages": total_pages,
    }})


@api_attempts_bp.route("/<attempt_id>", methods=["GET"])
@token_required
def detail(attempt_id):
    user = request.current_user
    db = current_app.db
    attempt = get_attempt(db, attempt_id, user.get_id())

    if not attempt:
        return jsonify({"ok": False, "error": "Attempt not found."}), 404

    return jsonify({"ok": True, "data": {"attempt": serialize_attempt(attempt)}})


@api_attempts_bp.route("/<attempt_id>/win", methods=["POST"])
@token_required
def win(attempt_id):
    user = request.current_user
    data = request.get_json(silent=True) or {}
    win_description = data.get("win_description", "")

    db = current_app.db
    new_state = toggle_win(db, attempt_id, user.get_id(), win_description)

    if new_state is None:
        return jsonify({"ok": False, "error": "Attempt not found."}), 404

    return jsonify({"ok": True, "data": {"unexpected_win": new_state}})


@api_attempts_bp.route("/<attempt_id>/reflection", methods=["POST"])
@token_required
def reflection(attempt_id):
    user = request.current_user
    data = request.get_json(silent=True) or {}

    reflection_asked = data.get("reflection_asked", "")
    reflection_learned = data.get("reflection_learned", "")
    reflection_control = data.get("reflection_control", "")

    db = current_app.db
    updated = update_reflection(
        db, attempt_id, user.get_id(),
        reflection_asked, reflection_learned, reflection_control,
    )

    if not updated:
        return jsonify({"ok": False, "error": "Attempt not found."}), 404

    return jsonify({"ok": True, "data": {"success": True}})
