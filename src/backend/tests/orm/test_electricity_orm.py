import pytest
import orm.electricity_orm as orm

ElectricityOrm = orm.ElectricityOrm


@pytest.fixture
def call_log():
    return {"execute_query": [], "execute_update": []}


@pytest.fixture(autouse=True)
def patch_mysql(monkeypatch, call_log):
    def fake_execute_query(query, params=()):
        q = " ".join(query.split())
        call_log["execute_query"].append((q, params))

        if "FROM Electricite" in q and "WHERE plug_type = %s" in q:
            plug = params[0]
            if plug == "C":
                return [{"plug_type": "C", "plug_png": "c.png", "sock_png": "c_s.png"}]
            return []

        if "FROM Electricite" in q and "ORDER BY plug_type" in q:
            return [
                {"plug_type": "C", "plug_png": "c.png", "sock_png": "c_s.png"},
                {"plug_type": "F", "plug_png": "f.png", "sock_png": "f_s.png"},
            ]

        return []

    def fake_execute_update(query, params=()):
        q = " ".join(query.split())
        call_log["execute_update"].append((q, params))

        if q.startswith("REPLACE INTO Electricite"):
            return 1
        if q.startswith("INSERT IGNORE INTO Electricite"):
            return 1
        if q.startswith("UPDATE Electricite SET"):
            return 1
        if q.startswith("DELETE FROM Electricite"):
            return 1 if params and params[0] else 0
        return 0

    monkeypatch.setattr(
        orm.MySQLConnection, "execute_query", staticmethod(fake_execute_query)
    )
    monkeypatch.setattr(
        orm.MySQLConnection, "execute_update", staticmethod(fake_execute_update)
    )


def test_find_by_plug_type_trouve(call_log):
    row = ElectricityOrm.find_by_plug_type("C")
    assert row and row["plug_type"] == "C"
    q, p = call_log["execute_query"][-1]
    assert "FROM Electricite" in q and "WHERE plug_type = %s" in q and p == ("C",)


def test_find_by_plug_type_pas_trouve():
    assert ElectricityOrm.find_by_plug_type("X") is None


def test_find_all(call_log):
    rows = ElectricityOrm.find_all()
    assert isinstance(rows, list) and len(rows) >= 2
    assert "ORDER BY plug_type" in call_log["execute_query"][-1][0]


def test_create_or_replace(call_log):
    n = ElectricityOrm.create_or_replace("C", "c.png", "c_s.png")
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert q.startswith("REPLACE INTO Electricite") and p == ("C", "c.png", "c_s.png")


def test_insert_ignore(call_log):
    n = ElectricityOrm.insert_ignore("F", "f.png", "f_s.png")
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert q.startswith("INSERT IGNORE INTO Electricite") and p == (
        "F",
        "f.png",
        "f_s.png",
    )


def test_update_partial_un_champ(call_log):
    n = ElectricityOrm.update_partial("C", {"plug_png": "new.png"})
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert "UPDATE Electricite SET plug_png = %s WHERE plug_type = %s" in q
    assert p == ("new.png", "C")


def test_update_partial_deux_champs_et_ignore_inconnus(call_log):
    n = ElectricityOrm.update_partial(
        "C", {"plug_png": "x.png", "sock_png": "y.png", "foo": "bar"}
    )
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert (
        "UPDATE Electricite SET" in q and "plug_png = %s" in q and "sock_png = %s" in q
    )
    assert p[-1] == "C" and set(p[:-1]) == {"x.png", "y.png"}


def test_update_partial_aucun_champ(call_log):
    before = len(call_log["execute_update"])
    n = ElectricityOrm.update_partial("C", {"foo": "bar"})
    after = len(call_log["execute_update"])
    assert n == 0 and after == before


def test_delete(call_log):
    n = ElectricityOrm.delete("F")
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert q.startswith("DELETE FROM Electricite") and p == ("F",)
