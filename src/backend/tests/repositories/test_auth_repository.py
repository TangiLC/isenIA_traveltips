# test_auth_repository.py
# pytest -q
# Prérequis conseillés : pip install pytest pytest-mock

import types
import builtins
import pytest

import orm.auth_orm as repo

AuthOrm = repo.AuthOrm


@pytest.fixture(autouse=True)
def patch_db_error(monkeypatch):
    """
    Dans le code, les blocs try/except attrapent mysql.connector.Error.
    On le remplace par une Exception locale pour ne pas dépendre du paquet mysql.
    """

    class DBError(Exception):
        pass

    monkeypatch.setattr(repo, "Error", DBError)
    return DBError


@pytest.fixture
def call_log():
    return {"execute_query": [], "execute_update": [], "commit": 0, "rollback": 0}


@pytest.fixture(autouse=True)
def patch_mysql(monkeypatch, call_log):
    """
    On monkeypatch les méthodes de MySQLConnection importées dans le module testé.
    Chaque fake enregistre ses appels dans call_log pour assertions.
    """

    def fake_execute_query(q, params=()):
        call_log["execute_query"].append((q, params))
        return []

    def fake_execute_update(q, params=()):
        call_log["execute_update"].append((q, params))
        return 0

    def fake_commit():
        call_log["commit"] += 1

    def fake_rollback():
        call_log["rollback"] += 1

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_query", staticmethod(fake_execute_query)
    )
    monkeypatch.setattr(
        repo.MySQLConnection, "execute_update", staticmethod(fake_execute_update)
    )
    monkeypatch.setattr(repo.MySQLConnection, "commit", staticmethod(fake_commit))
    monkeypatch.setattr(repo.MySQLConnection, "rollback", staticmethod(fake_rollback))


def test_row_to_user_out_minimal():
    row = {"id": 1, "pseudo": "alice", "role": "user", "password": "x"}
    out = AuthOrm.row_to_user_out(row)
    assert out == {"id": 1, "pseudo": "alice", "role": "user"}


def test_get_by_name_found(monkeypatch, call_log):
    def fake_execute_query(q, params=()):
        call_log["execute_query"].append((q, params))
        return [{"id": 1, "pseudo": "alice", "password": "hash", "role": "user"}]

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_query", staticmethod(fake_execute_query)
    )

    row = AuthOrm.get_by_name("alice")

    assert row["id"] == 1
    assert "FROM Utilisateurs" in call_log["execute_query"][0][0]
    assert call_log["execute_query"][0][1] == ("alice",)


def test_get_by_name_not_found(call_log):
    row = AuthOrm.get_by_name("nobody")
    assert row is None
    assert call_log["execute_query"]  # appelé une fois
    q, params = call_log["execute_query"][-1]
    assert "WHERE pseudo = %s" in q and params == ("nobody",)


def test_get_by_id_found(monkeypatch, call_log):
    def fake_execute_query(q, params=()):
        call_log["execute_query"].append((q, params))
        return [{"id": 5, "pseudo": "bob", "password": "hash", "role": "admin"}]

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_query", staticmethod(fake_execute_query)
    )

    row = AuthOrm.get_by_id(5)

    assert row["pseudo"] == "bob"
    assert call_log["execute_query"][-1][1] == (5,)


def test_create_success(monkeypatch, call_log):
    def fake_execute_update(q, params=()):
        call_log["execute_update"].append((q, params))
        return 1

    def fake_execute_query(q, params=()):
        call_log["execute_query"].append((q, params))
        # LAST_INSERT_ID()
        return [{"id": 42}]

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_update", staticmethod(fake_execute_update)
    )
    monkeypatch.setattr(
        repo.MySQLConnection, "execute_query", staticmethod(fake_execute_query)
    )

    new_id = AuthOrm.create("neo", "pwdhash", "user")

    assert new_id == 42
    assert call_log["commit"] == 1
    assert call_log["rollback"] == 0
    q1, p1 = call_log["execute_update"][0]
    assert "INSERT INTO Utilisateurs" in q1
    assert p1 == ("neo", "pwdhash", "user")
    # Vérifie qu'on a bien demandé le LAST_INSERT_ID
    assert any("LAST_INSERT_ID" in q for q, _ in call_log["execute_query"])


def test_create_error_rolls_back(monkeypatch, call_log, patch_db_error):
    def failing_update(q, params=()):
        call_log["execute_update"].append((q, params))
        raise patch_db_error("boom")

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_update", staticmethod(failing_update)
    )

    with pytest.raises(patch_db_error):
        AuthOrm.create("neo", "pwdhash", "user")

    assert call_log["rollback"] == 1
    assert call_log["commit"] == 0


def test_update_full_success(monkeypatch, call_log):
    def fake_update(q, params=()):
        call_log["execute_update"].append((q, params))
        return 1  # 1 ligne affectée

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_update", staticmethod(fake_update)
    )

    ok = AuthOrm.update_full(9, "alice", "h", "user")

    assert ok is True
    assert call_log["commit"] == 1
    q, p = call_log["execute_update"][-1]
    assert (
        "UPDATE Utilisateurs" in q and "SET pseudo = %s, password = %s, role = %s" in q
    )
    assert p == ("alice", "h", "user", 9)


def test_update_full_no_row(monkeypatch, call_log):
    def fake_update(q, params=()):
        call_log["execute_update"].append((q, params))
        return 0  # aucune ligne affectée

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_update", staticmethod(fake_update)
    )

    ok = AuthOrm.update_full(9, "alice", "h", "user")

    assert ok is False
    assert call_log["commit"] == 1


def test_update_full_error_rolls_back(monkeypatch, call_log, patch_db_error):
    def failing_update(q, params=()):
        call_log["execute_update"].append((q, params))
        raise patch_db_error("db down")

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_update", staticmethod(failing_update)
    )

    with pytest.raises(patch_db_error):
        AuthOrm.update_full(1, "u", "p", "r")

    assert call_log["rollback"] == 1
    assert call_log["commit"] == 0


def test_update_partial_builds_dynamic_set(monkeypatch, call_log):
    def fake_update(q, params=()):
        call_log["execute_update"].append((q, params))
        # on vérifie la requête dynamique
        assert "SET pseudo = %s, role = %s" in q or "SET role = %s, pseudo = %s" in q
        assert params[-1] == 12
        return 1

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_update", staticmethod(fake_update)
    )

    ok = AuthOrm.update_partial(12, pseudo="zz", role="admin")

    assert ok is True
    assert call_log["commit"] == 1


def test_update_partial_password_only(monkeypatch, call_log):
    def fake_update(q, params=()):
        call_log["execute_update"].append((q, params))
        assert "password = %s" in q and "pseudo" not in q and "role" not in q
        assert params == ("h2", 7)
        return 1

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_update", staticmethod(fake_update)
    )

    ok = AuthOrm.update_partial(7, password="h2")

    assert ok is True
    assert call_log["commit"] == 1


def test_update_partial_no_fields_no_query(monkeypatch, call_log):
    """
    Si rien n'est passé, la fonction retourne False et ne doit pas appeler execute_update.
    """

    def bomb(*args, **kwargs):
        raise AssertionError("execute_update ne devrait pas être appelé")

    monkeypatch.setattr(repo.MySQLConnection, "execute_update", staticmethod(bomb))

    ok = AuthOrm.update_partial(1)

    assert ok is False
    assert call_log["commit"] == 0
    assert call_log["execute_update"] == []


def test_update_partial_error_rolls_back(monkeypatch, call_log, patch_db_error):
    def failing_update(q, params=()):
        call_log["execute_update"].append((q, params))
        raise patch_db_error("oops")

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_update", staticmethod(failing_update)
    )

    with pytest.raises(patch_db_error):
        AuthOrm.update_partial(3, role="user")

    assert call_log["rollback"] == 1
    assert call_log["commit"] == 0


def test_delete_success(monkeypatch, call_log):
    def fake_update(q, params=()):
        call_log["execute_update"].append((q, params))
        return 1

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_update", staticmethod(fake_update)
    )

    ok = AuthOrm.delete(33)

    assert ok is True
    assert call_log["commit"] == 1
    q, p = call_log["execute_update"][-1]
    assert "DELETE FROM Utilisateurs" in q and p == (33,)


def test_delete_not_found(monkeypatch, call_log):
    def fake_update(q, params=()):
        call_log["execute_update"].append((q, params))
        return 0

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_update", staticmethod(fake_update)
    )

    ok = AuthOrm.delete(404)

    assert ok is False
    assert call_log["commit"] == 1


def test_delete_error_rolls_back(monkeypatch, call_log, patch_db_error):
    def failing_update(q, params=()):
        call_log["execute_update"].append((q, params))
        raise patch_db_error("nope")

    monkeypatch.setattr(
        repo.MySQLConnection, "execute_update", staticmethod(failing_update)
    )

    with pytest.raises(patch_db_error):
        AuthOrm.delete(1)

    assert call_log["rollback"] == 1
    assert call_log["commit"] == 0
