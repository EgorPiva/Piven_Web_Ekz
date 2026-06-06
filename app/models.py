from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    description = db.Column(db.String(120), nullable=False)

    users = db.relationship("User", back_populates="role")


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    middle_name = db.Column(db.String(64))
    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )

    role = db.relationship("Role", back_populates="users")
    reviews = db.relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    visits = db.relationship(
        "BookVisit",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(part for part in parts if part)

    def has_role(self, *roles):
        return self.role is not None and self.role.name in roles


class Cover(db.Model):
    __tablename__ = "covers"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(80), nullable=False)
    md5_hash = db.Column(db.String(32), unique=True, nullable=False)

    books = db.relationship("Book", back_populates="cover")


book_genres = db.Table(
    "book_genres",
    db.Column(
        "book_id",
        db.Integer,
        db.ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "genre_id",
        db.Integer,
        db.ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    publisher = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    pages = db.Column(db.Integer, nullable=False)
    cover_id = db.Column(
        db.Integer,
        db.ForeignKey("covers.id", ondelete="CASCADE"),
        nullable=False,
    )

    cover = db.relationship("Cover", back_populates="books")
    genres = db.relationship("Genre", secondary=book_genres, back_populates="books")
    reviews = db.relationship(
        "Review",
        back_populates="book",
        cascade="all, delete-orphan",
    )
    visits = db.relationship(
        "BookVisit",
        back_populates="book",
        cascade="all, delete-orphan",
    )

    @property
    def average_rating(self):
        if not self.reviews:
            return None
        return round(sum(review.rating for review in self.reviews) / len(self.reviews), 1)


class Genre(db.Model):
    __tablename__ = "genres"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    books = db.relationship("Book", secondary=book_genres, back_populates="genres")


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(
        db.Integer,
        db.ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    book = db.relationship("Book", back_populates="reviews")
    user = db.relationship("User", back_populates="reviews")

    __table_args__ = (
        db.CheckConstraint("rating BETWEEN 0 AND 5", name="reviews_rating_range"),
        db.UniqueConstraint("book_id", "user_id", name="reviews_book_user_unique"),
    )


class BookVisit(db.Model):
    __tablename__ = "book_visits"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(
        db.Integer,
        db.ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    anonymous_key = db.Column(db.String(36), nullable=True)
    visited_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    book = db.relationship("Book", back_populates="visits")
    user = db.relationship("User", back_populates="visits")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
