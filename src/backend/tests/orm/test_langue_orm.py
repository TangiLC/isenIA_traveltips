import pytest
import orm.langue_orm as orm

LangueOrm = orm.LangueOrm


@pytest.fixture
def call_log():
    return {"execute_query": [], "execute_update": []}


@pytest.fixture(autouse=True)
def patch_mysql(monkeypatch, call_log):
    def fake_execute_query(query, params=()):
        q = " ".join(query.split())
        call_log["execute_query"].append((q, params))

        if (
            "FROM Langues l" in q
            and "LEFT JOIN Familles f" in q
            and "WHERE l.iso639_2 = %s" in q
        ):
            code = params[0]
            if code == "fra":
                return [
                    {
                        "iso639_2": "fra",
                        "name_en": "French",
                        "name_fr": "Français",
                        "name_local": "Français",
                        "is_in_mongo": 1,
                        "branche_en": "Indo-European",
                        "branche_fr": "Indo-européen",
                    }
                ]
            return []

        if (
            "LOWER(l.name_en) LIKE LOWER(%s)" in q
            and "LOWER(l.name_fr) LIKE LOWER(%s)" in q
            and "LOWER(l.name_local) LIKE LOWER(%s)" in q
        ):
            pat1, pat2, pat3 = params
            assert pat1 == pat2 == pat3
            if "fr" in pat1.lower():
                return [
                    {
                        "iso639_2": "fra",
                        "name_en": "French",
                        "name_fr": "Français",
                        "name_local": "Français",
                        "is_in_mongo": 1,
                        "branche_en": "Indo-European",
                        "branche_fr": "Indo-européen",
                    }
                ]
            return []

        if (
            "INNER JOIN Familles f ON l.famille_id = f.id" in q
            and "LOWER(f.branche_en) LIKE LOWER (%s)" in q
        ):
            pat_en, pat_fr = params
            assert pat_en == pat_fr
            if "indo" in pat_en.lower():
                return [
                    {
                        "iso639_2": "fra",
                        "name_en": "French",
                        "name_fr": "Français",
                        "name_local": "Français",
                        "is_in_mongo": 1,
                        "branche_en": "Indo-European",
                        "branche_fr": "Indo-européen",
                    }
                ]
            return []

        if "SELECT id FROM Familles" in q:
            v1, v2 = params
            assert v1 == v2
            if v1 and "indo-european" in v1.lower():
                return [{"id": 7}]
            return []

        return []

    def fake_execute_update(query, params=()):
        q = " ".join(query.split())
        call_log["execute_update"].append((q, params))

        if q.startswith("REPLACE INTO Langues"):
            return 1
        if q.startswith("UPDATE Langues SET"):
            return 1
        if q.startswith("DELETE FROM Langues"):
            return 1 if params and params[0] else 0
        if q.startswith("INSERT INTO Langues"):
            return 1
        return 0

    monkeypatch.setattr(
        orm.MySQLConnection, "execute_query", staticmethod(fake_execute_query)
    )
    monkeypatch.setattr(
        orm.MySQLConnection, "execute_update", staticmethod(fake_execute_update)
    )


def test_find_by_iso639_2_trouve(call_log):
    row = LangueOrm.find_by_iso639_2("fra")
    assert row and row["iso639_2"] == "fra"
    q, p = call_log["execute_query"][-1]
    assert "FROM Langues l" in q and "LEFT JOIN Familles f" in q and p == ("fra",)


def test_find_by_iso639_2_pas_trouve():
    assert LangueOrm.find_by_iso639_2("xxx") is None


def test_find_by_name_like(call_log):
    out = LangueOrm.find_by_name("Fr")
    assert isinstance(out, list) and out and out[0]["iso639_2"] == "fra"
    q, p = call_log["execute_query"][-1]
    assert "LOWER(l.name_en) LIKE LOWER(%s)" in q and p[0] == p[1] == p[2]
    assert p[0].startswith("%") and p[0].endswith("%")


def test_find_by_famille_like(call_log):
    out = LangueOrm.find_by_famille("indo")
    assert isinstance(out, list) and out and out[0]["iso639_2"] == "fra"
    q, p = call_log["execute_query"][-1]
    assert "INNER JOIN Familles" in q and p[0] == p[1]


def test_get_famille_id_by_branche_trouve(call_log):
    fam_id = LangueOrm.get_famille_id_by_branche("Indo-European")
    assert fam_id == 7
    q, p = call_log["execute_query"][-1]
    assert "SELECT id FROM Familles" in q and p[0] == p[1]


def test_get_famille_id_by_branche_pas_trouve():
    assert LangueOrm.get_famille_id_by_branche("Unknown") is None


def test_create_or_replace(call_log):
    n = LangueOrm.create_or_replace(
        "fra", "French", "Français", "Français", "Indo-European", 1
    )
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert q.startswith("REPLACE INTO Langues")
    assert p[0] == "fra" and p[1] == "French"


def test_update_partial_un_champ(call_log):
    n = LangueOrm.update_partial("fra", {"name_en": "French"})
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert "UPDATE Langues SET name_en = %s WHERE iso639_2 = %s" in q
    assert p == ("French", "fra")


def test_update_partial_plusieurs_champs_et_ignore_inconnus(call_log):
    n = LangueOrm.update_partial(
        "fra", {"name_fr": "Français", "name_local": "Français", "foo": "bar"}
    )
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert "UPDATE Langues SET" in q and "name_fr = %s" in q and "name_local = %s" in q
    assert p[-1] == "fra"
    assert set(p[:-1]) == {"Français", "Français"}


def test_update_partial_aucun_champ(call_log):
    before = len(call_log["execute_update"])
    n = LangueOrm.update_partial("fra", {"foo": "bar"})
    after = len(call_log["execute_update"])
    assert n == 0 and after == before


def test_insert_ignore(call_log):
    n = LangueOrm.insert_ignore(
        "eng", "English", "Anglais", "English", "Indo-European", 1
    )
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert q.startswith("INSERT INTO Langues")
    assert p[0] == "eng"


def test_delete(call_log):
    n = LangueOrm.delete("fra")
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert q.startswith("DELETE FROM Langues") and p == ("fra",)
