from flask import Blueprint, request, jsonify
from utils.jwt_auth import token_required
from data.opportunities import OPPORTUNITIES

api_library_bp = Blueprint("api_library", __name__, url_prefix="/api/library")


@api_library_bp.route("", methods=["GET"])
@token_required
def index():
    domain = request.args.get("domain", "")
    difficulty = request.args.get("difficulty", "")

    filtered = OPPORTUNITIES
    if domain:
        filtered = [o for o in filtered if domain in o["domains"]]
    if difficulty:
        try:
            diff_int = int(difficulty)
            filtered = [o for o in filtered if o["difficulty"] == diff_int]
        except ValueError:
            pass

    all_domains = sorted(set(d for o in OPPORTUNITIES for d in o["domains"]))

    return jsonify({"ok": True, "data": {
        "opportunities": filtered,
        "all_domains": all_domains,
    }})
