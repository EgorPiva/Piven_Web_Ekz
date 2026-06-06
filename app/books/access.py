from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                flash(
                    "Для выполнения данного действия необходимо пройти процедуру аутентификации",
                    "warning",
                )
                return redirect(url_for("auth.login"))
            if not current_user.has_role(*roles):
                flash("У вас недостаточно прав для выполнения данного действия", "danger")
                return redirect(url_for("books.index"))
            return view(*args, **kwargs)

        return wrapped_view

    return decorator
