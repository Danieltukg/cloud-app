"""
Vertex — REST API для каталога горных вершин.

Эндпоинты:
    GET    /api/health           — проверка живости (для healthcheck/k8s probes)
    GET    /api/peaks            — список вершин (?search=, ?country=, ?range=, ?sort=)
    GET    /api/peaks/<id>       — одна вершина
    POST   /api/peaks            — создать
    PUT    /api/peaks/<id>       — обновить
    DELETE /api/peaks/<id>       — удалить
    GET    /api/stats            — агрегированная статистика
    GET    /api/meta             — справочники (страны, хребты) для фильтров

CLI:
    flask --app app seed         — засеять начальные данные
"""
import os
import time

import click
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import func
from sqlalchemy.exc import OperationalError

from config import Config
from models import Peak, db
from seed import SEED_PEAKS

load_dotenv()

# Путь к фронтенду (../frontend относительно backend/)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)

    CORS(app)
    db.init_app(app)

    with app.app_context():
        if app.config["AUTO_CREATE_DB"]:
            _wait_for_db(
                retries=app.config["DB_WAIT_RETRIES"],
                delay=app.config["DB_WAIT_DELAY"],
            )
            db.create_all()
            if app.config["AUTO_SEED"]:
                seed_if_empty()

    register_routes(app)
    register_cli(app)
    return app


def _wait_for_db(retries: int = 15, delay: float = 2.0) -> None:
    """Postgres в контейнере может стартовать дольше бэкенда — ждём его."""
    for attempt in range(1, retries + 1):
        try:
            db.session.execute(db.text("SELECT 1"))
            return
        except OperationalError:
            print(f"[vertex] БД недоступна, попытка {attempt}/{retries}…", flush=True)
            time.sleep(delay)
    raise RuntimeError("Не удалось подключиться к базе данных")


def seed_if_empty() -> int:
    """Засеять данные, если таблица пуста. Возвращает число добавленных строк."""
    if db.session.query(Peak).count() == 0:
        db.session.add_all(Peak(**row) for row in SEED_PEAKS)
        db.session.commit()
        print(f"[vertex] Засеяно вершин: {len(SEED_PEAKS)}", flush=True)
        return len(SEED_PEAKS)
    return 0


# --- Валидация ------------------------------------------------------------

REQUIRED = ("name", "height_m", "country", "range_name")


def _validate(payload: dict, *, partial: bool = False) -> tuple[dict, list[str]]:
    errors: list[str] = []
    data: dict = {}

    def present(key):
        return key in payload and payload[key] not in (None, "")

    for key in REQUIRED:
        if not partial and not present(key):
            errors.append(f"Поле '{key}' обязательно")

    if present("name"):
        data["name"] = str(payload["name"]).strip()[:120]
    if present("country"):
        data["country"] = str(payload["country"]).strip()[:80]
    if present("range_name"):
        data["range_name"] = str(payload["range_name"]).strip()[:120]
    if present("difficulty"):
        data["difficulty"] = str(payload["difficulty"]).strip()[:40]
    if present("summary"):
        data["summary"] = str(payload["summary"]).strip()

    if present("height_m"):
        try:
            h = int(payload["height_m"])
            if not 0 < h < 9000:
                errors.append("Высота должна быть в диапазоне 1–8999 м")
            else:
                data["height_m"] = h
        except (TypeError, ValueError):
            errors.append("Высота должна быть числом")

    if present("first_ascent_year"):
        try:
            data["first_ascent_year"] = int(payload["first_ascent_year"])
        except (TypeError, ValueError):
            errors.append("Год первого восхождения должен быть числом")

    return data, errors


# --- Маршруты -------------------------------------------------------------

def register_routes(app: Flask) -> None:

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/health")
    def health():
        try:
            db.session.execute(db.text("SELECT 1"))
            return jsonify(status="ok", db="up")
        except OperationalError:
            return jsonify(status="degraded", db="down"), 503

    @app.get("/api/peaks")
    def list_peaks():
        q = db.session.query(Peak)

        search = request.args.get("search", "").strip()
        country = request.args.get("country", "").strip()
        rng = request.args.get("range", "").strip()
        sort = request.args.get("sort", "height_desc")

        if search:
            like = f"%{search}%"
            q = q.filter(db.or_(Peak.name.ilike(like), Peak.summary.ilike(like)))
        if country:
            q = q.filter(Peak.country == country)
        if rng:
            q = q.filter(Peak.range_name == rng)

        sorts = {
            "height_desc": Peak.height_m.desc(),
            "height_asc": Peak.height_m.asc(),
            "name": Peak.name.asc(),
            "year": Peak.first_ascent_year.asc(),
        }
        q = q.order_by(sorts.get(sort, Peak.height_m.desc()))

        return jsonify([p.to_dict() for p in q.all()])

    @app.get("/api/peaks/<int:peak_id>")
    def get_peak(peak_id: int):
        peak = db.session.get(Peak, peak_id)
        if not peak:
            return jsonify(error="Вершина не найдена"), 404
        return jsonify(peak.to_dict())

    @app.post("/api/peaks")
    def create_peak():
        payload = request.get_json(silent=True) or {}
        data, errors = _validate(payload)
        if errors:
            return jsonify(errors=errors), 422
        if db.session.query(Peak).filter_by(name=data["name"]).first():
            return jsonify(errors=["Вершина с таким названием уже есть"]), 409
        peak = Peak(**data)
        db.session.add(peak)
        db.session.commit()
        return jsonify(peak.to_dict()), 201

    @app.put("/api/peaks/<int:peak_id>")
    def update_peak(peak_id: int):
        peak = db.session.get(Peak, peak_id)
        if not peak:
            return jsonify(error="Вершина не найдена"), 404
        payload = request.get_json(silent=True) or {}
        data, errors = _validate(payload, partial=True)
        if errors:
            return jsonify(errors=errors), 422
        for key, value in data.items():
            setattr(peak, key, value)
        db.session.commit()
        return jsonify(peak.to_dict())

    @app.delete("/api/peaks/<int:peak_id>")
    def delete_peak(peak_id: int):
        peak = db.session.get(Peak, peak_id)
        if not peak:
            return jsonify(error="Вершина не найдена"), 404
        db.session.delete(peak)
        db.session.commit()
        return "", 204

    @app.get("/api/stats")
    def stats():
        total = db.session.query(func.count(Peak.id)).scalar() or 0
        highest = db.session.query(func.max(Peak.height_m)).scalar() or 0
        countries = db.session.query(func.count(func.distinct(Peak.country))).scalar() or 0
        avg = db.session.query(func.avg(Peak.height_m)).scalar() or 0
        return jsonify(
            total=total,
            highest=highest,
            countries=countries,
            avg_height=round(float(avg)),
        )

    @app.get("/api/meta")
    def meta():
        countries = [c[0] for c in db.session.query(Peak.country).distinct().order_by(Peak.country)]
        ranges = [r[0] for r in db.session.query(Peak.range_name).distinct().order_by(Peak.range_name)]
        return jsonify(countries=countries, ranges=ranges)


# --- CLI ------------------------------------------------------------------

def register_cli(app: Flask) -> None:
    @app.cli.command("seed")
    def seed_command():
        """Засеять начальные данные (если база пуста)."""
        added = seed_if_empty()
        click.echo(f"Добавлено вершин: {added}" if added else "База уже не пуста — пропуск.")


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
