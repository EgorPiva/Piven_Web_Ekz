from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("books.index"))

    if request.method == "POST":
        login_value = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"
        user = User.query.filter_by(login=login_value).first()

        if user is not None and user.check_password(password):
            login_user(user, remember=remember)
            flash("Вы успешно вошли в систему", "success")
            return redirect(request.args.get("next") or url_for("books.index"))

        flash(
            "Невозможно аутентифицироваться с указанными логином и паролем",
            "danger",
        )

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы", "info")
    return redirect(url_for("books.index"))
