import os

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
        from app.models import Genre, Role, User

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

        db.session.commit()
        print("Exam data initialized.")
        print("Admin login/password: admin/admin")
        print("Moderator login/password: moderator/moderator")
        print("User login/password: user/user")
