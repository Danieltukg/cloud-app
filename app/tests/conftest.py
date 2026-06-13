"""Общие фикстуры pytest."""
import os
import sys

import pytest

# Делаем backend/ импортируемым независимо от рабочего каталога
BACKEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, BACKEND)

from app import create_app, seed_if_empty  # noqa: E402
from models import db  # noqa: E402


@pytest.fixture
def app(tmp_path):
    """Свежее приложение на временном SQLite-файле для каждого теста."""
    db_file = tmp_path / "test.db"
    application = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
            "AUTO_CREATE_DB": True,
            "AUTO_SEED": False,
            "TESTING": True,
        }
    )
    with application.app_context():
        seed_if_empty()  # 10 стартовых вершин
    yield application
    with application.app_context():
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()
