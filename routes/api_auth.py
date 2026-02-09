from flask import Blueprint, request, jsonify, current_app
from models.user import create_user, find_user_by_email, verify_password
from utils.jwt_auth import generate_token

api_auth_bp = Blueprint("api_auth", __name__, url_prefix="/api/auth")


@api_auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    display_name = data.get("display_name", "").strip()
    quest_domain = data.get("quest_domain", "general")

    if not email or not password or not display_name:
        return jsonify({"ok": False, "error": "All fields are required."}), 400

    if len(password) < 6:
        return jsonify({"ok": False, "error": "Password must be at least 6 characters."}), 400

    db = current_app.db
    existing = find_user_by_email(db, email)
    if existing:
        return jsonify({"ok": False, "error": "An account with that email already exists."}), 409

    user = create_user(db, email, password, display_name, quest_domain)
    token = generate_token(user.get_id())

    return jsonify({"ok": True, "data": {"token": token, "user": user.to_dict()}}), 201


@api_auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"ok": False, "error": "Email and password are required."}), 400

    db = current_app.db
    user = find_user_by_email(db, email)
    if not user or not verify_password(user, password):
        return jsonify({"ok": False, "error": "Invalid email or password."}), 401

    token = generate_token(user.get_id())
    return jsonify({"ok": True, "data": {"token": token, "user": user.to_dict()}})
