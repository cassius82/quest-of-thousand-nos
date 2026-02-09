from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from datetime import datetime, timezone
from utils.jwt_auth import token_required
from data.opportunities import OPPORTUNITIES
from data.opportunities_expanded import EXPANDED_OPPORTUNITIES
from data.generator import get_opportunities_for_user, get_all_valid_combinations

api_library_bp = Blueprint("api_library", __name__, url_prefix="/api/library")


@api_library_bp.route("", methods=["GET"])
@token_required
def index():
    domain = request.args.get("domain", "")
    difficulty = request.args.get("difficulty", "")
    source = request.args.get("source", "")
    count = request.args.get("count", 10, type=int)
    count = max(1, min(50, count))

    user = request.current_user
    db = current_app.db

    # Filter helper
    def _filter(items, domain_filter, diff_filter):
        result = items
        if domain_filter:
            result = [o for o in result if domain_filter in o["domains"]]
        if diff_filter:
            try:
                diff_int = int(diff_filter)
                result = [o for o in result if o["difficulty"] == diff_int]
            except ValueError:
                pass
        return result

    diff_int = None
    if difficulty:
        try:
            diff_int = int(difficulty)
        except ValueError:
            pass

    if source == "generated":
        generated = get_opportunities_for_user(
            db, user.get_id(), count=count,
            domain=domain or None,
            difficulty=diff_int,
        )
        return jsonify({"ok": True, "data": {"generated": generated}})

    curated = _filter(OPPORTUNITIES, domain, difficulty)
    expanded = _filter(EXPANDED_OPPORTUNITIES, domain, difficulty)
    generated = get_opportunities_for_user(
        db, user.get_id(), count=count,
        domain=domain or None,
        difficulty=diff_int,
    )

    all_domains = sorted(set(
        d for olist in [OPPORTUNITIES, EXPANDED_OPPORTUNITIES]
        for o in olist for d in o["domains"]
    ))

    categories = sorted(set(o.get("category", "") for o in EXPANDED_OPPORTUNITIES if o.get("category")))

    return jsonify({"ok": True, "data": {
        "curated": curated,
        "expanded": expanded,
        "generated": generated,
        "categories": categories,
        "all_domains": all_domains,
        "opportunities": curated + expanded,
    }})


@api_library_bp.route("/generate", methods=["GET"])
@token_required
def generate():
    user = request.current_user
    db = current_app.db

    count = request.args.get("count", 10, type=int)
    count = max(1, min(50, count))
    domain = request.args.get("domain", "") or None
    difficulty = request.args.get("difficulty", "")

    diff_int = None
    if difficulty:
        try:
            diff_int = int(difficulty)
        except ValueError:
            pass

    generated = get_opportunities_for_user(
        db, user.get_id(), count=count,
        domain=domain,
        difficulty=diff_int,
    )

    total_combos = len(get_all_valid_combinations())
    completed_count = db.completed_combos.count_documents({"user_id": ObjectId(user.get_id())})

    return jsonify({"ok": True, "data": {
        "generated": generated,
        "total_available": total_combos,
        "completed": completed_count,
        "remaining": total_combos - completed_count,
    }})


@api_library_bp.route("/complete", methods=["POST"])
@token_required
def complete():
    user = request.current_user
    db = current_app.db
    data = request.get_json(silent=True) or {}

    combo_id = data.get("combo_id", "").strip()
    if not combo_id:
        return jsonify({"ok": False, "error": "combo_id is required."}), 400

    attempt_id = data.get("attempt_id")

    try:
        db.completed_combos.insert_one({
            "user_id": ObjectId(user.get_id()),
            "combo_id": combo_id,
            "completed_at": datetime.now(timezone.utc),
            "attempt_id": ObjectId(attempt_id) if attempt_id else None,
        })
    except Exception:
        # Duplicate — already completed
        pass

    return jsonify({"ok": True, "data": {"combo_id": combo_id}})
