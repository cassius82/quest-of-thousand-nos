import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/quest_of_thousand_nos")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", os.environ.get("SECRET_KEY", "dev-jwt-secret"))
    JWT_EXPIRATION_DAYS = int(os.environ.get("JWT_EXPIRATION_DAYS", "30"))
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
