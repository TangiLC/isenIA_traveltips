import pytest
from datetime import date
from types import SimpleNamespace

import orm.week_meteo_orm as orm

WeekMeteoOrm = orm.WeekMeteoOrm


@pytest.fixture
def call_log():
    return {"execute_query": [], "execute_update": [], "commit": 0, "connect": 0}


@pytest.fixture(autouse=True)
def patch_mysql_and_models(monkeypatch, call_log):
    # Neutralise le modèle: retourne le dict source
    monkeypatch.setattr(orm.WeekMeteo, "from_dict", staticmethod(lambda d: d))

    def fake_connect():
        call_log["connect"] += 1

    def fake_commit():
        call_log["commit"] += 1

    def fake_execute_query(query, params=()):
        q = " ".join(query.split())
        call_log["execute_query"].append((q, params))

        # get_by_pk
        if (
            "FROM Meteo_Weekly" in q
            and "WHERE geoname_id = %s AND week_start_date = %s" in q
        ):
            gid, d = params
            return [
                {
                    "geoname_id": gid,
                    "week_start_date": d,
                    "week_end_date": date.fromordinal(d.toordinal() + 6),
                    "temperature_max_avg": 25.0,
                    "temperature_min_avg": 15.0,
                    "precipitation_sum": 5.0,
                }
            ]

        # get_range full
        if "FROM Meteo_Weekly" in q and "AND week_start_date >= %s" in q:
            gid, sd, ed = params
            days = [
                sd,
                date.fromordinal(sd.toordinal() + 7),
                date.fromordinal(sd.toordinal() + 14),
            ]
            return [
                {
                    "geoname_id": gid,
                    "week_start_date": d,
                    "week_end_date": date.fromordinal(d.toordinal() + 6),
                    "temperature_max_avg": 20.0 + i,
                    "temperature_min_avg": 10.0 + i,
                    "precipitation_sum": 1.0 * i,
                }
                for i, d in enumerate(days)
                if d <= ed
            ]

        # get_range only by gid
        if "FROM Meteo_Weekly" in q and "WHERE geoname_id = %s" in q and "AND" not in q:
            gid = params[0]
            days = [date(2024, 1, 1), date(2024, 1, 8)]
            return [
                {
                    "geoname_id": gid,
                    "week_start_date": d,
                    "week_end_date": date.fromordinal(d.toordinal() + 6),
                    "temperature_max_avg": 20.0 + i,
                    "temperature_min_avg": 10.0 + i,
                    "precipitation_sum": 2.0 * i,
                }
                for i, d in enumerate(days)
            ]

        # get_all
        if "FROM Meteo_Weekly" in q and "ORDER BY geoname_id, week_start_date" in q:
            limit, offset = params
            data = [
                {
                    "geoname_id": 1,
                    "week_start_date": date(2024, 1, 1),
                    "week_end_date": date(2024, 1, 7),
                    "temperature_max_avg": 21.0,
                    "temperature_min_avg": 11.0,
                    "precipitation_sum": 0.0,
                },
                {
                    "geoname_id": 2,
                    "week_start_date": date(2024, 1, 1),
                    "week_end_date": date(2024, 1, 7),
                    "temperature_max_avg": 22.0,
                    "temperature_min_avg": 12.0,
                    "precipitation_sum": 1.0,
                },
            ]
            return data[offset : offset + limit]

        # get_existing_geoname_ids
        if q.strip() == "SELECT DISTINCT geoname_id FROM Meteo_Weekly":
            return [{"geoname_id": 10}, {"geoname_id": 20}, {"geoname_id": 10}]

        return []

    def fake_execute_update(query, params=()):
        q = " ".join(query.split())
        call_log["execute_update"].append((q, params))
        if (
            isinstance(params, (list, tuple))
            and params
            and isinstance(params[0], (list, tuple))
        ):
            return len(params)  # executemany simulé
        return 1

    monkeypatch.setattr(orm.MySQLConnection, "connect", staticmethod(fake_connect))
    monkeypatch.setattr(orm.MySQLConnection, "commit", staticmethod(fake_commit))
    monkeypatch.setattr(
        orm.MySQLConnection, "execute_query", staticmethod(fake_execute_query)
    )
    monkeypatch.setattr(
        orm.MySQLConnection, "execute_update", staticmethod(fake_execute_update)
    )


def test_get_by_pk_trouve(call_log):
    d = date(2024, 1, 1)
    row = WeekMeteoOrm.get_by_pk(123, d)
    assert row["geoname_id"] == 123 and row["week_start_date"] == d
    q, p = call_log["execute_query"][-1]
    assert "WHERE geoname_id = %s AND week_start_date = %s" in q and p == (123, d)


def test_get_range_avec_bornes(call_log):
    sd, ed = date(2024, 1, 1), date(2024, 1, 20)
    rows = WeekMeteoOrm.get_range(5, sd, ed)
    assert rows and rows[0]["geoname_id"] == 5
    assert all(sd <= r["week_start_date"] <= ed for r in rows)


def test_get_range_sans_bornes(call_log):
    rows = WeekMeteoOrm.get_range(7, None, None)
    assert len(rows) == 2
    q, _ = call_log["execute_query"][-1]
    assert "WHERE geoname_id = %s" in q and "AND week_start_date" not in q


def test_get_all_pagination(call_log):
    rows = WeekMeteoOrm.get_all(skip=1, limit=1)
    assert len(rows) == 1
    assert "ORDER BY geoname_id, week_start_date" in call_log["execute_query"][-1][0]


def test_get_existing_geoname_ids_set(call_log):
    s = WeekMeteoOrm.get_existing_geoname_ids()
    assert s == {10, 20}


def test_upsert_refetch_et_commit(call_log):
    item = SimpleNamespace(
        geoname_id=9,
        week_start_date=date(2024, 2, 5),
        week_end_date=date(2024, 2, 11),
        temperature_max_avg=23.0,
        temperature_min_avg=13.0,
        precipitation_sum=3.0,
    )
    row = WeekMeteoOrm.upsert(item)
    assert row["geoname_id"] == 9 and call_log["commit"] >= 1
    assert any("INSERT INTO Meteo_Weekly" in q for q, _ in call_log["execute_update"])


def test_bulk_upsert_vecteur(call_log):
    items = [
        SimpleNamespace(
            geoname_id=1,
            week_start_date=date(2024, 1, 1),
            week_end_date=date(2024, 1, 7),
            temperature_max_avg=21.0,
            temperature_min_avg=11.0,
            precipitation_sum=1.0,
        ),
        SimpleNamespace(
            geoname_id=2,
            week_start_date=date(2024, 1, 8),
            week_end_date=date(2024, 1, 14),
            temperature_max_avg=22.0,
            temperature_min_avg=12.0,
            precipitation_sum=2.0,
        ),
    ]
    n = WeekMeteoOrm.bulk_upsert(items)
    assert n == 2
    q, p = call_log["execute_update"][-1]
    assert "INSERT INTO Meteo_Weekly" in q and isinstance(p, list) and len(p) == 2
    assert call_log["commit"] >= 1


def test_delete_true_si_supprime(call_log):
    ok = WeekMeteoOrm.delete(3, date(2024, 1, 1))
    assert ok is True
    q, p = call_log["execute_update"][-1]
    assert q.startswith("DELETE FROM Meteo_Weekly") and p[0] == 3
