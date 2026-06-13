"""Модели базы данных (SQLAlchemy)."""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Peak(db.Model):
    """Горная вершина."""

    __tablename__ = "peaks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    height_m = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(80), nullable=False)
    range_name = db.Column(db.String(120), nullable=False)
    first_ascent_year = db.Column(db.Integer, nullable=True)
    difficulty = db.Column(db.String(40), nullable=False, default="—")
    summary = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "height_m": self.height_m,
            "country": self.country,
            "range_name": self.range_name,
            "first_ascent_year": self.first_ascent_year,
            "difficulty": self.difficulty,
            "summary": self.summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
