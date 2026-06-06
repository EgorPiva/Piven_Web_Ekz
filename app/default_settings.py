import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

SECRET_KEY = "replace-this-key-in-instance-config"
SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(BASE_DIR, "instance", "exam.sqlite"),
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads", "covers")
MAX_CONTENT_LENGTH = 8 * 1024 * 1024
ALLOWED_COVER_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
STUDENT_GROUP = "241-371"
STUDENT_NAME = "Пивень Егор"
