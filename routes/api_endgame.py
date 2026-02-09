from flask import Blueprint, request, jsonify, current_app
from utils.jwt_auth import token_required
from models.attempt import get_endgame_stats

api_endgame_bp = Blueprint("api_endgame", __name__, url_prefix="/api/endgame")


@api_endgame_bp.route("", methods=["GET"])
@token_required
def index():
    user = request.current_user

    if not user.has_completed:
        return jsonify({"ok": False, "error": "Quest not yet complete."}), 403

    db = current_app.db
    stats = get_endgame_stats(db, user.get_id())

    # Serialize aggregation results (ObjectId-free, but _id is a string date/domain)
    daily = [{"date": d["_id"], "nos": d["nos"], "attempts": d["attempts"], "wins": d["wins"]} for d in stats["daily"]]
    domains = [{"domain": d["_id"], "nos": d["nos"], "attempts": d["attempts"]} for d in stats["domains"]]

    return jsonify({"ok": True, "data": {
        "user": user.to_dict(),
        "daily": daily,
        "domains": domains,
    }})
