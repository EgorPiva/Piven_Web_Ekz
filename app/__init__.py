import os
import hashlib

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Для выполнения данного действия необходимо пройти процедуру аутентификации"
login_manager.login_message_category = "warning"


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.from_object("app.default_settings")
    app.config.from_pyfile("config.py", silent=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.auth.routes import auth_bp
    from app.books.routes import books_bp
    from app.main.routes import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)

    register_cli(app)

    return app


def register_cli(app):
    @app.cli.command("init-exam")
    def init_exam():
        from app.models import Book, Cover, Genre, Role, User

        db.create_all()

        roles = {
            "admin": "администратор",
            "moderator": "модератор",
            "user": "пользователь",
        }
        for name, description in roles.items():
            if Role.query.filter_by(name=name).first() is None:
                db.session.add(Role(name=name, description=description))

        genres = (
            "Роман",
            "Фантастика",
            "Детектив",
            "Научная литература",
            "История",
            "Учебная литература",
        )
        for name in genres:
            if Genre.query.filter_by(name=name).first() is None:
                db.session.add(Genre(name=name))

        db.session.flush()
        admin_role = Role.query.filter_by(name="admin").first()
        if User.query.filter_by(login="admin").first() is None:
            db.session.add(
                User(
                    login="admin",
                    password_hash=generate_password_hash("admin"),
                    last_name="Администратор",
                    first_name="Системы",
                    middle_name="",
                    role=admin_role,
                )
            )

        moderator_role = Role.query.filter_by(name="moderator").first()
        user_role = Role.query.filter_by(name="user").first()
        demo_users = (
            {
                "login": "moderator",
                "password": "moderator",
                "last_name": "Модератор",
                "first_name": "Тест",
                "middle_name": "",
                "role": moderator_role,
            },
            {
                "login": "user",
                "password": "user",
                "last_name": "Пользователь",
                "first_name": "Тест",
                "middle_name": "",
                "role": user_role,
            },
        )
        for payload in demo_users:
            if User.query.filter_by(login=payload["login"]).first() is None:
                db.session.add(
                    User(
                        login=payload["login"],
                        password_hash=generate_password_hash(payload["password"]),
                        last_name=payload["last_name"],
                        first_name=payload["first_name"],
                        middle_name=payload["middle_name"],
                        role=payload["role"],
                    )
                )

        db.session.flush()
        seed_demo_books()

        db.session.commit()
        print("Exam data initialized.")
        print("Admin login/password: admin/admin")
        print("Moderator login/password: moderator/moderator")
        print("User login/password: user/user")


def seed_demo_books():
    from app.models import Book, Cover, Genre

    demo_books = (
        {
            "title": "Серый архив",
            "description": "Городской детектив о библиотекаре, который находит в каталоге книги скрытые послания и следы исчезнувшего фонда.",
            "year": 2019,
            "publisher": "Вымышленное издательство",
            "author": "Андрей Лесной",
            "pages": 384,
            "genres": ("Детектив", "История"),
            "cover_name": "demo-archive.svg",
            "cover_color": "#1f2937",
            "accent_color": "#f59e0b",
        },
        {
            "title": "Окно в июль",
            "description": "Лирический роман о летнем доме у озера, где старые письма меняют судьбы нескольких поколений одной семьи.",
            "year": 2021,
            "publisher": "Лаборатория текста",
            "author": "Марина Светлова",
            "pages": 256,
            "genres": ("Роман",),
            "cover_name": "demo-july.svg",
            "cover_color": "#0f766e",
            "accent_color": "#fde68a",
        },
        {
            "title": "Алгоритмы тумана",
            "description": "Научно-популярная книга о том, как машинное обучение ищет закономерности там, где человеку видится хаос.",
            "year": 2023,
            "publisher": "Наука и взгляд",
            "author": "Илья Романов",
            "pages": 312,
            "genres": ("Научная литература", "Учебная литература"),
            "cover_name": "demo-fog.svg",
            "cover_color": "#3730a3",
            "accent_color": "#93c5fd",
        },
        {
            "title": "Хроники северного порта",
            "description": "Исторический роман о городе, который растет вместе с морем, торговлей и тремя поколениями одного капитанского рода.",
            "year": 2018,
            "publisher": "Берег книги",
            "author": "Ольга Ветрова",
            "pages": 420,
            "genres": ("История", "Роман"),
            "cover_name": "demo-port.svg",
            "cover_color": "#7c2d12",
            "accent_color": "#fdba74",
        },
        {
            "title": "Тайна шестой полки",
            "description": "Детектив о пропавшем каталоге редких изданий, где каждая подсказка спрятана в заметках на полях.",
            "year": 2020,
            "publisher": "Новые истории",
            "author": "Павел Громов",
            "pages": 336,
            "genres": ("Детектив", "Роман"),
            "cover_name": "demo-shelf.svg",
            "cover_color": "#111827",
            "accent_color": "#c084fc",
        },
        {
            "title": "Учебник спокойных решений",
            "description": "Практическое пособие о том, как системно подходить к задачам, не теряя ясности мышления и внимания к деталям.",
            "year": 2022,
            "publisher": "Школьная мастерская",
            "author": "Екатерина Лазарева",
            "pages": 228,
            "genres": ("Учебная литература",),
            "cover_name": "demo-study.svg",
            "cover_color": "#155e75",
            "accent_color": "#67e8f9",
        },
    )

    genres_by_name = {genre.name: genre for genre in Genre.query.all()}
    upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "static", "uploads", "covers")
    os.makedirs(upload_folder, exist_ok=True)

    for data in demo_books:
        if Book.query.filter_by(title=data["title"]).first() is not None:
            continue

        cover = Cover.query.filter_by(filename=data["cover_name"]).first()
        if cover is None:
            svg_content = build_demo_cover_svg(
                title=data["title"],
                author=data["author"],
                color=data["cover_color"],
                accent=data["accent_color"],
            )
            file_path = os.path.join(upload_folder, data["cover_name"])
            with open(file_path, "w", encoding="utf-8") as cover_file:
                cover_file.write(svg_content)

            cover = Cover(
                filename=data["cover_name"],
                mime_type="image/svg+xml",
                md5_hash=hashlib.md5(svg_content.encode("utf-8")).hexdigest(),
            )
            db.session.add(cover)
            db.session.flush()

        book = Book(
            title=data["title"],
            description=data["description"],
            year=data["year"],
            publisher=data["publisher"],
            author=data["author"],
            pages=data["pages"],
            cover=cover,
        )
        book.genres = [genres_by_name[name] for name in data["genres"] if name in genres_by_name]
        db.session.add(book)


def build_demo_cover_svg(title, author, color, accent):
    safe_title = escape_xml(title)
    safe_author = escape_xml(author)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="900" viewBox="0 0 600 900">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="{color}" />
      <stop offset="100%" stop-color="#0f172a" />
    </linearGradient>
  </defs>
  <rect width="600" height="900" fill="url(#bg)" />
  <rect x="48" y="48" width="504" height="804" rx="28" fill="none" stroke="{accent}" stroke-width="8" opacity="0.8" />
  <circle cx="486" cy="132" r="46" fill="{accent}" opacity="0.16" />
  <path d="M112 180h376" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.7" />
  <text x="80" y="280" fill="#f8fafc" font-family="Georgia, serif" font-size="54" font-weight="700">{safe_title}</text>
  <text x="80" y="350" fill="#cbd5e1" font-family="Arial, sans-serif" font-size="26">Автор: {safe_author}</text>
  <text x="80" y="790" fill="#e2e8f0" font-family="Arial, sans-serif" font-size="24">Демо-издание для экзамена</text>
</svg>
"""


def escape_xml(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
