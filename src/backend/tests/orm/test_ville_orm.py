import pytest
from types import SimpleNamespace

import orm.ville_orm as orm

VilleOrm = orm.VilleOrm


@pytest.fixture
def call_log():
    return {"execute_query": [], "execute_update": [], "commit": 0, "connect": 0}


@pytest.fixture(autouse=True)
def patch_mysql_and_models(monkeypatch, call_log):
    # Neutralise model: on retourne simplement le dict source
    monkeypatch.setattr(orm.Ville, "from_dict", staticmethod(lambda d: d))

    def fake_connect():
        call_log["connect"] += 1

    def fake_commit():
        call_log["commit"] += 1

    def fake_execute_query(query, params=()):
        q = " ".join(query.split())
        call_log["execute_query"].append((q, params))

        # get_by_geoname_id
        if "FROM Villes WHERE geoname_id = %s" in q:
            gid = params[0]
            return [
                {
                    "geoname_id": gid,
                    "name_en": "X",
                    "latitude": 1.0,
                    "longitude": 2.0,
                    "country_3166a2": "FR",
                    "is_capital": 1,
                }
            ]

        # get_by_name (LIKE)
        if "FROM Villes WHERE LOWER(name_en) LIKE LOWER(%s)" in q:
            pat = params[0]
            if "par" in pat.lower():
                return [
                    {
                        "geoname_id": 1,
                        "name_en": "Paris",
                        "latitude": 48.85,
                        "longitude": 2.35,
                        "country_3166a2": "FR",
                        "is_capital": 1,
                    },
                    {
                        "geoname_id": 2,
                        "name_en": "Parma",
                        "latitude": 44.8,
                        "longitude": 10.3,
                        "country_3166a2": "IT",
                        "is_capital": 0,
                    },
                ]
            return []

        # get_by_country
        if "FROM Villes WHERE country_3166a2 = %s" in q:
            iso = params[0]
            return [
                {
                    "geoname_id": 10,
                    "name_en": "CityA",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "country_3166a2": iso,
                    "is_capital": 0,
                },
                {
                    "geoname_id": 11,
                    "name_en": "CityB",
                    "latitude": 1.0,
                    "longitude": 1.0,
                    "country_3166a2": iso,
                    "is_capital": 1,
                },
            ]

        # get_all LIMIT/OFFSET
        if "FROM Villes LIMIT %s OFFSET %s" in q:
            limit, offset = params
            data = [
                {
                    "geoname_id": 100,
                    "name_en": "A",
                    "latitude": 0,
                    "longitude": 0,
                    "country_3166a2": "AD",
                    "is_capital": 0,
                },
                {
                    "geoname_id": 101,
                    "name_en": "B",
                    "latitude": 0,
                    "longitude": 0,
                    "country_3166a2": "AE",
                    "is_capital": 0,
                },
                {
                    "geoname_id": 102,
                    "name_en": "C",
                    "latitude": 0,
                    "longitude": 0,
                    "country_3166a2": "AF",
                    "is_capital": 0,
                },
            ]
            return data[offset : offset + limit]

        return []

    def fake_execute_update(query, params=()):
        q = " ".join(query.split())
        call_log["execute_update"].append((q, params))
        # renvoie 1 pour une écriture réussie, ou len(list) pour executemany
        if (
            isinstance(params, (list, tuple))
            and params
            and isinstance(params[0], (list, tuple))
        ):
            return len(params)
        return 1

    monkeypatch.setattr(orm.MySQLConnection, "connect", staticmethod(fake_connect))
    monkeypatch.setattr(orm.MySQLConnection, "commit", staticmethod(fake_commit))
    monkeypatch.setattr(
        orm.MySQLConnection, "execute_query", staticmethod(fake_execute_query)
    )
    monkeypatch.setattr(
        orm.MySQLConnection, "execute_update", staticmethod(fake_execute_update)
    )


def test_get_by_geoname_id(call_log):
    v = VilleOrm.get_by_geoname_id(123)
    assert v["geoname_id"] == 123
    q, p = call_log["execute_query"][-1]
    assert "FROM Villes WHERE geoname_id = %s" in q and p == (123,)


def test_get_by_name_like_insensible_casse(call_log):
    rows = VilleOrm.get_by_name("Par")
    assert isinstance(rows, list) and len(rows) == 2
    assert call_log["execute_query"][-1][1][0].startswith("%")  # pattern LIKE


def test_get_by_country_uppercase_param(call_log):
    rows = VilleOrm.get_by_country("fr")
    assert all(r["country_3166a2"] == "FR" for r in rows)


def test_get_all_pagination(call_log):
    rows = VilleOrm.get_all(skip=1, limit=1)
    assert len(rows) == 1
    assert "LIMIT %s OFFSET %s" in call_log["execute_query"][-1][0]


def test_create_inserts_puis_refetch(call_log):
    payload = {
        "geoname_id": 999,
        "name_en": "Neo",
        "latitude": 1.2,
        "longitude": 3.4,
        "country_3166a2": "FR",
        "is_capital": 0,
    }
    v = VilleOrm.create(payload)
    assert v["geoname_id"] == 999
    # Vérifie INSERT puis commit puis SELECT by id
    queries = [q for q, _ in call_log["execute_update"]]
    assert any("INSERT INTO Villes" in q for q in queries)
    assert call_log["commit"] >= 1
    assert any(
        "FROM Villes WHERE geoname_id = %s" in q for q, _ in call_log["execute_query"]
    )


def test_update_refuse_si_aucun_champ_modif(call_log, monkeypatch):
    # get_by_geoname_id retourne déjà un dict (via fake)
    res = VilleOrm.update(123, {"name_en": None})  # pas de champ modifiable
    assert res["geoname_id"] == 123
    # pas d'UPDATE
    assert not any(
        q.startswith("UPDATE Villes SET") for q, _ in call_log["execute_update"]
    )


def test_update_ok_build_set_and_commit(call_log):
    res = VilleOrm.update(123, {"name_en": "NewName", "latitude": 9.9})
    assert res["geoname_id"] == 123
    q, p = call_log["execute_update"][-1]
    assert "UPDATE Villes SET" in q and p[-1] == 123
    assert call_log["commit"] >= 1


def test_delete_true_quand_existe(call_log):
    ok = VilleOrm.delete(123)
    assert ok is True
    q, p = call_log["execute_update"][-1]
    assert q.startswith("DELETE FROM Villes") and p == (123,)
    assert call_log["commit"] >= 1


def test_bulk_insert_ignore_vectorise(call_log):
    items = [
        {
            "geoname_id": 1,
            "name_en": "A",
            "latitude": 0,
            "longitude": 0,
            "country_3166a2": "AD",
            "is_capital": 0,
        },
        {
            "geoname_id": 2,
            "name_en": "B",
            "latitude": 0,
            "longitude": 0,
            "country_3166a2": "AE",
            "is_capital": 0,
        },
        {
            "geoname_id": 3,
            "name_en": "C",
            "latitude": 0,
            "longitude": 0,
            "country_3166a2": "AF",
            "is_capital": 1,
        },
    ]
    n = VilleOrm.bulk_insert_ignore(items)
    assert n == 3  # executemany simulé
    q, p = call_log["execute_update"][-1]
    assert "INSERT INTO Villes" in q and isinstance(p, list) and len(p) == 3
    assert call_log["commit"] >= 1
