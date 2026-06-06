import hashlib
import os

import bleach
import markdown
from flask import current_app
from markupsafe import Markup
from werkzeug.utils import secure_filename

from app import db
from app.models import Cover, Genre

ALLOWED_MARKDOWN_TAGS = bleach.sanitizer.ALLOWED_TAGS.union(
    {
        "p",
        "br",
        "pre",
        "code",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "img",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
    }
)
ALLOWED_MARKDOWN_ATTRIBUTES = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
}


def allowed_cover(filename):
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in current_app.config["ALLOWED_COVER_EXTENSIONS"]


def clean_markdown(text):
    return bleach.clean(text or "", tags=[], strip=True)


def render_markdown(text):
    html = markdown.markdown(
        text or "",
        extensions=["extra", "nl2br", "sane_lists"],
        output_format="html5",
    )
    clean_html = bleach.clean(
        html,
        tags=ALLOWED_MARKDOWN_TAGS,
        attributes=ALLOWED_MARKDOWN_ATTRIBUTES,
        protocols=["http", "https", "mailto"],
        strip=True,
    )
    return Markup(clean_html)


def save_cover(file_storage):
    content = file_storage.read()
    file_storage.seek(0)
    digest = hashlib.md5(content).hexdigest()
    with db.session.no_autoflush:
        existing_cover = Cover.query.filter_by(md5_hash=digest).first()

    if existing_cover is not None:
        return existing_cover

    original = secure_filename(file_storage.filename)
    extension = original.rsplit(".", 1)[1].lower()
    cover = Cover(
        filename="pending",
        mime_type=file_storage.mimetype or "application/octet-stream",
        md5_hash=digest,
    )
    db.session.add(cover)
    db.session.flush()

    filename = f"{cover.id}.{extension}"
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    with open(os.path.join(upload_folder, filename), "wb") as cover_file:
        cover_file.write(content)

    cover.filename = filename
    return cover


def get_selected_genres(raw_ids):
    genre_ids = []
    for raw_id in raw_ids:
        try:
            genre_ids.append(int(raw_id))
        except (TypeError, ValueError):
            continue

    if not genre_ids:
        return []

    return Genre.query.filter(Genre.id.in_(genre_ids)).order_by(Genre.name).all()
