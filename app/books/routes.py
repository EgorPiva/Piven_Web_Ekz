import csv
import io
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, Response, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app import db
from app.books.access import roles_required
from app.books.utils import (
    allowed_cover,
    clean_markdown,
    get_selected_genres,
    render_markdown,
    save_cover,
)
from app.models import Book, BookVisit, Genre, Review, User

books_bp = Blueprint("books", __name__)

RATING_LABELS = {
    5: "отлично",
    4: "хорошо",
    3: "удовлетворительно",
    2: "неудовлетворительно",
    1: "плохо",
    0: "ужасно",
}


@books_bp.app_template_filter("markdown")
def markdown_filter(text):
    return render_markdown(text)


@books_bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    since = datetime.utcnow() - timedelta(days=90)
    visit_counts = (
        db.session.query(
            BookVisit.book_id.label("book_id"),
            func.count(BookVisit.id).label("visits_count"),
        )
        .filter(BookVisit.visited_at >= since)
        .group_by(BookVisit.book_id)
        .subquery()
    )
    popular_books = (
        db.session.query(Book, visit_counts.c.visits_count)
        .join(visit_counts, visit_counts.c.book_id == Book.id)
        .options(selectinload(Book.genres), selectinload(Book.cover))
        .order_by(visit_counts.c.visits_count.desc(), Book.title.asc())
        .limit(5)
        .all()
    )
    recent_books = get_recent_books()
    books = (
        Book.query.options(selectinload(Book.genres), selectinload(Book.reviews))
        .order_by(Book.year.desc(), Book.title.asc())
        .paginate(page=page, per_page=10, error_out=False)
    )
    return render_template(
        "books/index.html",
        books=books,
        popular_books=popular_books,
        recent_books=recent_books,
    )


@books_bp.route("/books/<int:book_id>")
def show(book_id):
    book = (
        Book.query.options(
            selectinload(Book.cover),
            selectinload(Book.genres),
            selectinload(Book.reviews).selectinload(Review.user),
        )
        .filter_by(id=book_id)
        .first_or_404()
    )
    record_book_visit(book)
    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(
            book_id=book.id,
            user_id=current_user.id,
        ).first()
    return render_template(
        "books/show.html",
        book=book,
        user_review=user_review,
        rating_labels=RATING_LABELS,
    )


@books_bp.route("/statistics")
@roles_required("admin")
def statistics():
    tab = request.args.get("tab", "log")
    page = request.args.get("page", 1, type=int)
    date_from, date_to = get_date_range()

    if tab == "views":
        stats = build_book_stats_query(date_from, date_to).paginate(
            page=page,
            per_page=10,
            error_out=False,
        )
        return render_template(
            "books/statistics.html",
            tab="views",
            stats=stats,
            visits=None,
            date_from=request.args.get("date_from", ""),
            date_to=request.args.get("date_to", ""),
        )

    visits = build_visit_log_query().paginate(page=page, per_page=10, error_out=False)
    return render_template(
        "books/statistics.html",
        tab="log",
        stats=None,
        visits=visits,
        date_from=request.args.get("date_from", ""),
        date_to=request.args.get("date_to", ""),
    )


@books_bp.route("/statistics/export")
@roles_required("admin")
def export_statistics():
    tab = request.args.get("tab", "log")
    date_from, date_to = get_date_range()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    if tab == "views":
        writer.writerow(["№", "Название книги", "Количество просмотров"])
        for index, row in enumerate(build_book_stats_query(date_from, date_to).all(), 1):
            writer.writerow([index, row.title, row.visits_count])
        filename = f"book_views_{datetime.utcnow().strftime('%Y-%m-%d')}.csv"
    else:
        writer.writerow(["№", "ФИО пользователя", "Название книги", "Дата и время просмотра"])
        for index, visit in enumerate(build_visit_log_query().all(), 1):
            user_name = visit.user.full_name if visit.user else "Неаутентифицированный пользователь"
            writer.writerow([index, user_name, visit.book.title, visit.visited_at.strftime("%d.%m.%Y %H:%M")])
        filename = f"visit_log_{datetime.utcnow().strftime('%Y-%m-%d')}.csv"

    csv_data = "\ufeff" + output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@books_bp.route("/books/new", methods=["GET", "POST"])
@roles_required("admin")
def create():
    genres = Genre.query.order_by(Genre.name).all()
    if request.method == "POST":
        book = Book()
        try:
            if fill_book_from_form(book, require_cover=True):
                db.session.add(book)
                db.session.commit()
                flash("Книга добавлена", "success")
                return redirect(url_for("books.show", book_id=book.id))
        except Exception as error:
            db.session.rollback()
            flash(f"Ошибка при сохранении книги: {error}", "danger")

    return render_template(
        "books/form.html",
        book=None,
        genres=genres,
        action="Добавить",
        form=request.form,
    )


@books_bp.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@roles_required("admin", "moderator")
def edit(book_id):
    book = Book.query.get_or_404(book_id)
    genres = Genre.query.order_by(Genre.name).all()
    if request.method == "POST":
        try:
            if fill_book_from_form(book, require_cover=False):
                db.session.commit()
                flash("Книга обновлена", "success")
                return redirect(url_for("books.show", book_id=book.id))
        except Exception as error:
            db.session.rollback()
            flash(f"Ошибка при сохранении книги: {error}", "danger")

    return render_template(
        "books/form.html",
        book=book,
        genres=genres,
        action="Сохранить",
        form=request.form,
    )


@books_bp.route("/books/<int:book_id>/delete", methods=["POST"])
@roles_required("admin")
def delete(book_id):
    book = Book.query.get_or_404(book_id)
    try:
        db.session.delete(book)
        db.session.commit()
        flash("Книга удалена", "info")
    except Exception as error:
        db.session.rollback()
        flash(f"Ошибка при удалении книги: {error}", "danger")
    return redirect(url_for("books.index"))


@books_bp.route("/books/<int:book_id>/reviews/new", methods=["GET", "POST"])
@login_required
def create_review(book_id):
    book = Book.query.get_or_404(book_id)
    existing_review = Review.query.filter_by(
        book_id=book.id,
        user_id=current_user.id,
    ).first()
    if existing_review is not None:
        flash("Вы уже оставили рецензию на эту книгу", "warning")
        return redirect(url_for("books.show", book_id=book.id))

    if request.method == "POST":
        rating = request.form.get("rating", type=int)
        text = clean_markdown(request.form.get("text", "").strip())

        if rating not in RATING_LABELS:
            flash("Выберите корректную оценку", "danger")
        elif not text:
            flash("Заполните текст рецензии", "danger")
        else:
            try:
                review = Review(
                    book=book,
                    user=current_user,
                    rating=rating,
                    text=text,
                )
                db.session.add(review)
                db.session.commit()
                flash("Рецензия добавлена", "success")
                return redirect(url_for("books.show", book_id=book.id))
            except Exception as error:
                db.session.rollback()
                flash(f"Ошибка при сохранении рецензии: {error}", "danger")

    return render_template(
        "books/review_form.html",
        book=book,
        rating_labels=RATING_LABELS,
        form=request.form,
    )


def get_anonymous_key():
    if "anonymous_key" not in session:
        session["anonymous_key"] = str(uuid.uuid4())
    return session["anonymous_key"]


def record_book_visit(book):
    now = datetime.utcnow()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    query = BookVisit.query.filter(
        BookVisit.book_id == book.id,
        BookVisit.visited_at >= day_start,
        BookVisit.visited_at < day_end,
    )
    if current_user.is_authenticated:
        query = query.filter(BookVisit.user_id == current_user.id)
        visit = BookVisit(book=book, user=current_user)
    else:
        anonymous_key = get_anonymous_key()
        query = query.filter(BookVisit.anonymous_key == anonymous_key)
        visit = BookVisit(book=book, anonymous_key=anonymous_key)

    if query.count() >= 10:
        return

    db.session.add(visit)
    db.session.commit()


def get_recent_books():
    query = BookVisit.query.options(selectinload(BookVisit.book).selectinload(Book.genres))
    if current_user.is_authenticated:
        query = query.filter(BookVisit.user_id == current_user.id)
    else:
        anonymous_key = session.get("anonymous_key")
        if not anonymous_key:
            return []
        query = query.filter(BookVisit.anonymous_key == anonymous_key)

    visits = query.order_by(BookVisit.visited_at.desc()).all()
    recent_books = []
    seen_books = set()
    for visit in visits:
        if visit.book_id in seen_books:
            continue
        recent_books.append(visit.book)
        seen_books.add(visit.book_id)
        if len(recent_books) == 5:
            break
    return recent_books


def build_visit_log_query():
    return (
        BookVisit.query.options(selectinload(BookVisit.book), selectinload(BookVisit.user))
        .order_by(BookVisit.visited_at.desc(), BookVisit.id.desc())
    )


def build_book_stats_query(date_from=None, date_to=None):
    visit_counts = (
        db.session.query(
            BookVisit.book_id.label("book_id"),
            func.count(BookVisit.id).label("visits_count"),
        )
        .filter(BookVisit.user_id.isnot(None))
    )
    if date_from:
        visit_counts = visit_counts.filter(BookVisit.visited_at >= date_from)
    if date_to:
        visit_counts = visit_counts.filter(BookVisit.visited_at < date_to)
    visit_counts = visit_counts.group_by(BookVisit.book_id).subquery()
    return (
        db.session.query(Book.title, visit_counts.c.visits_count)
        .join(visit_counts, visit_counts.c.book_id == Book.id)
        .order_by(visit_counts.c.visits_count.desc(), Book.title.asc())
    )


def get_date_range():
    date_from = parse_date(request.args.get("date_from"))
    date_to = parse_date(request.args.get("date_to"))
    if date_to:
        date_to = date_to + timedelta(days=1)
    return date_from, date_to


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def fill_book_from_form(book, require_cover):
    title = request.form.get("title", "").strip()
    description = clean_markdown(request.form.get("description", "").strip())
    year = request.form.get("year", type=int)
    publisher = request.form.get("publisher", "").strip()
    author = request.form.get("author", "").strip()
    pages = request.form.get("pages", type=int)
    cover_file = request.files.get("cover")
    selected_genres = get_selected_genres(request.form.getlist("genres"))

    if not all([title, description, year, publisher, author, pages]):
        flash("Заполните все обязательные поля", "danger")
        return False
    if year < 1450 or year > 2100:
        flash("Укажите корректный год издания", "danger")
        return False
    if pages < 1:
        flash("Количество страниц должно быть положительным", "danger")
        return False
    if not selected_genres:
        flash("Выберите хотя бы один жанр", "danger")
        return False
    if require_cover and (cover_file is None or cover_file.filename == ""):
        flash("Загрузите обложку книги", "danger")
        return False
    if cover_file and cover_file.filename and not allowed_cover(cover_file.filename):
        flash("Файл обложки должен быть изображением png, jpg, jpeg, gif или webp", "danger")
        return False

    book.title = title
    book.description = description
    book.year = year
    book.publisher = publisher
    book.author = author
    book.pages = pages
    if cover_file and cover_file.filename:
        book.cover = save_cover(cover_file)

    book.genres = selected_genres

    return True
