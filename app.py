from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient

from config import Config
from models.user import ensure_indexes


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS
    CORS(app, origins=app.config["CORS_ORIGINS"].split(","))

    # MongoDB
    client = MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=5000)
    db_name = app.config["MONGO_URI"].rsplit("/", 1)[-1].split("?")[0] or "quest_of_thousand_nos"
    app.db = client[db_name]

    # Create indexes lazily on first request
    @app.before_request
    def _ensure_indexes():
        if not getattr(app, '_indexes_created', False):
            try:
                ensure_indexes(app.db)
                app._indexes_created = True
            except Exception:
                pass

    # Register API blueprints
    from routes.api_auth import api_auth_bp
    from routes.api_user import api_user_bp
    from routes.api_attempts import api_attempts_bp
    from routes.api_library import api_library_bp
    from routes.api_endgame import api_endgame_bp

    app.register_blueprint(api_auth_bp)
    app.register_blueprint(api_user_bp)
    app.register_blueprint(api_attempts_bp)
    app.register_blueprint(api_library_bp)
    app.register_blueprint(api_endgame_bp)

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
