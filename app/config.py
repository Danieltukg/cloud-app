"""Конфигурация приложения. Всё берётся из окружения (12-factor)."""
import os


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _database_uri() -> str:
    """URL из окружения, иначе локальный SQLite (запуск без инфраструктуры)."""
    url = os.getenv("DATABASE_URL")
    if url:
        # SQLAlchemy ждёт postgresql://, а не postgres://
        return url.replace("postgres://", "postgresql://", 1)
    return "sqlite:///vertex.db"


class Config:
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    # Создавать таблицы при старте (db.create_all).
    # В проде с Alembic выставляй AUTO_CREATE_DB=false и катай миграции.
    AUTO_CREATE_DB = _bool(os.getenv("AUTO_CREATE_DB"), default=True)

    # Засеивать начальные данные, если база пуста.
    AUTO_SEED = _bool(os.getenv("AUTO_SEED"), default=True)

    # Сколько ждать готовности БД на старте (контейнеры стартуют не мгновенно).
    DB_WAIT_RETRIES = int(os.getenv("DB_WAIT_RETRIES", "15"))
    DB_WAIT_DELAY = float(os.getenv("DB_WAIT_DELAY", "2.0"))
