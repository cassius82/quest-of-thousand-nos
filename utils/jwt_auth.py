import hashlib
from datetime import date, datetime, timezone, timedelta
from functools import wraps

import jwt
from flask import request, jsonify, current_app

from data.quotes import QUOTES
from models.user import find_user_by_id


def generate_token(user_id):
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=current_app.config["JWT_EXPIRATION_DAYS"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token):
    try:
        payload = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"ok": False, "error": "Missing or invalid token."}), 401

        token = auth_header[7:]
        user_id = decode_token(token)
        if not user_id:
            return jsonify({"ok": False, "error": "Invalid or expired token."}), 401

        user = find_user_by_id(current_app.db, user_id)
        if not user:
            return jsonify({"ok": False, "error": "User not found."}), 401

        request.current_user = user
        return f(*args, **kwargs)

    return decorated


def get_daily_quote(user_id):
    seed = f"{user_id}-{date.today().isoformat()}"
    idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(QUOTES)
    return QUOTES[idx]
