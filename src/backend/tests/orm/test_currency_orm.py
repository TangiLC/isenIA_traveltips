import pytest
import orm.currency_orm as orm


CurrencyOrm = orm.CurrencyOrm


@pytest.fixture
def call_log():
    return {
        "execute_query": [],
        "execute_update": [],
    }


@pytest.fixture(autouse=True)
def patch_mysql(monkeypatch, call_log):
    def fake_execute_query(query, params=()):
        q = " ".join(query.split())
        call_log["execute_query"].append((q, params))

        # Réponses simulées selon la requête
        if "FROM Monnaies" in q and "WHERE iso4217 = %s" in q:
            code = params[0]
            if code == "EUR":
                return [{"iso4217": "EUR", "name": "Euro", "symbol": "€"}]
            return []
        if "LOWER(name) LIKE LOWER(%s)" in q and "LOWER(symbol) LIKE LOWER(%s)" in q:
            pattern1, pattern2 = params
            # renvoie 2 lignes factices si le pattern contient "eur"
            if "eur" in pattern1.lower() or "eur" in pattern2.lower():
                return [
                    {"iso4217": "EUR", "name": "Euro", "symbol": "€"},
                    {"iso4217": "XEU", "name": "European Currency Unit", "symbol": "₠"},
                ]
            return []
        return []

    def fake_execute_update(query, params=()):
        q = " ".join(query.split())
        call_log["execute_update"].append((q, params))

        if q.startswith("REPLACE INTO Monnaies"):
            # 1 ligne affectée
            return 1
        if q.startswith("INSERT IGNORE INTO Monnaies"):
            return 1
        if q.startswith("UPDATE Monnaies SET"):
            # retourne nb lignes affectées (1)
            return 1
        if q.startswith("DELETE FROM Monnaies"):
            return 1 if params and params[0] else 0
        return 0

    monkeypatch.setattr(
        orm.MySQLConnection, "execute_query", staticmethod(fake_execute_query)
    )
    monkeypatch.setattr(
        orm.MySQLConnection, "execute_update", staticmethod(fake_execute_update)
    )


def test_find_by_iso4217_trouve(call_log):
    row = CurrencyOrm.find_by_iso4217("EUR")
    assert row and row["iso4217"] == "EUR"
    q, p = call_log["execute_query"][-1]
    assert "FROM Monnaies" in q and "WHERE iso4217 = %s" in q
    assert p == ("EUR",)


def test_find_by_iso4217_pas_trouve(call_log):
    row = CurrencyOrm.find_by_iso4217("XXX")
    assert row is None
    q, p = call_log["execute_query"][-1]
    assert p == ("XXX",)


def test_find_by_name_or_symbol_like_insensible_casse(call_log):
    out = CurrencyOrm.find_by_name_or_symbol("EuR")
    assert isinstance(out, list) and len(out) == 2
    q, p = call_log["execute_query"][-1]
    assert "LOWER(name) LIKE LOWER(%s)" in q and "LOWER(symbol) LIKE LOWER(%s)" in q
    assert p[0].startswith("%") and p[0].endswith("%")
    assert p[0] == p[1]  # même pattern pour name et symbol


def test_create_or_replace_ok(call_log):
    n = CurrencyOrm.create_or_replace("EUR", "Euro", "€")
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert q.startswith("REPLACE INTO Monnaies")
    assert p == ("EUR", "Euro", "€")


def test_insert_ignore_ok(call_log):
    n = CurrencyOrm.insert_ignore("USD", "US Dollar", "$")
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert q.startswith("INSERT IGNORE INTO Monnaies")
    assert p == ("USD", "US Dollar", "$")


def test_update_partial_name_uniquement(call_log):
    n = CurrencyOrm.update_partial("EUR", {"name": "Euro"})
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert q.startswith("UPDATE Monnaies SET")
    assert "name = %s" in q and "symbol" not in q
    assert p == ("Euro", "EUR")


def test_update_partial_symbol_uniquement(call_log):
    n = CurrencyOrm.update_partial("EUR", {"symbol": "€"})
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert "symbol = %s" in q and "name" not in q
    assert p == ("€", "EUR")


def test_update_partial_deux_champs_et_ignore_inconnus(call_log):
    n = CurrencyOrm.update_partial("EUR", {"symbol": "€", "name": "Euro", "foo": "bar"})
    assert n == 1
    q, p = call_log["execute_update"][-1]
    # Les champs autorisés sont name, symbol ; foo est ignoré
    assert "UPDATE Monnaies SET" in q
    assert "symbol = %s" in q and "name = %s" in q
    # l'ordre dépend de l'ordre d'insertion du dict ; on vérifie la cohérence des paramètres
    assert p[-1] == "EUR"
    assert set(p[:-1]) == {"€", "Euro"}


def test_update_partial_aucun_champ_autorise_ne_fait_rien(call_log, monkeypatch):
    # Si aucun champ autorisé, on doit retourner 0 et ne pas appeler execute_update
    before = len(call_log["execute_update"])
    n = CurrencyOrm.update_partial("EUR", {"foo": "bar"})
    after = len(call_log["execute_update"])
    assert n == 0
    assert after == before  # pas d'appel à execute_update


def test_delete_ok(call_log):
    n = CurrencyOrm.delete("EUR")
    assert n == 1
    q, p = call_log["execute_update"][-1]
    assert q.startswith("DELETE FROM Monnaies") and p == ("EUR",)
