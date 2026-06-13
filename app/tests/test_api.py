"""Тесты REST API каталога вершин."""


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["db"] == "up"


def test_list_seeded(client):
    r = client.get("/api/peaks")
    assert r.status_code == 200
    peaks = r.get_json()
    assert len(peaks) == 10
    # сортировка по умолчанию — по убыванию высоты
    assert peaks[0]["height_m"] >= peaks[-1]["height_m"]


def test_sort_by_name(client):
    names = [p["name"] for p in client.get("/api/peaks?sort=name").get_json()]
    assert names == sorted(names)


def test_search_filters(client):
    # ILIKE в Postgres регистронезависим и для кириллицы; SQLite складывает
    # регистр только для ASCII, поэтому в тесте берём совпадающий регистр.
    r = client.get("/api/peaks?search=Эверест")
    data = r.get_json()
    assert len(data) == 1
    assert "Эверест" in data[0]["name"]


def test_create_peak(client):
    payload = {
        "name": "Рысы",
        "height_m": 2503,
        "country": "Польша / Словакия",
        "range_name": "Татры",
    }
    r = client.post("/api/peaks", json=payload)
    assert r.status_code == 201
    body = r.get_json()
    assert body["id"]
    assert body["name"] == "Рысы"
    assert client.get("/api/peaks").get_json().__len__() == 11


def test_create_validation_errors(client):
    r = client.post("/api/peaks", json={"name": "X"})
    assert r.status_code == 422
    assert len(r.get_json()["errors"]) == 3  # height, country, range


def test_create_bad_height(client):
    r = client.post(
        "/api/peaks",
        json={"name": "Y", "height_m": 99999, "country": "C", "range_name": "R"},
    )
    assert r.status_code == 422


def test_duplicate_name_conflict(client):
    payload = {"name": "Дубль", "height_m": 1000, "country": "C", "range_name": "R"}
    assert client.post("/api/peaks", json=payload).status_code == 201
    assert client.post("/api/peaks", json=payload).status_code == 409


def test_get_missing_404(client):
    assert client.get("/api/peaks/99999").status_code == 404


def test_update_peak(client):
    pid = client.get("/api/peaks").get_json()[0]["id"]
    r = client.put(f"/api/peaks/{pid}", json={"difficulty": "Тестовая"})
    assert r.status_code == 200
    assert r.get_json()["difficulty"] == "Тестовая"


def test_delete_peak(client):
    pid = client.get("/api/peaks").get_json()[0]["id"]
    assert client.delete(f"/api/peaks/{pid}").status_code == 204
    assert client.get(f"/api/peaks/{pid}").status_code == 404


def test_stats(client):
    s = client.get("/api/stats").get_json()
    assert s["total"] == 10
    assert s["highest"] == 8849
    assert s["countries"] >= 1


def test_meta(client):
    m = client.get("/api/meta").get_json()
    assert "Гималаи" in m["ranges"]
    assert isinstance(m["countries"], list)
