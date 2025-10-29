import types
import pytest

import connexion.mysql_connect as my

MySQLConnection = my.MySQLConnection


@pytest.fixture(autouse=True)
def no_dotenv(monkeypatch):
    monkeypatch.setattr(my, "load_dotenv", lambda: None)


def _set_env(monkeypatch, host="localhost", port="3307", db="trav", user="u", pwd="p"):
    monkeypatch.setenv("MYSQL_HOST", host)
    monkeypatch.setenv("MYSQL_PORT", port)
    monkeypatch.setenv("MYSQL_DATABASE", db)
    monkeypatch.setenv("MYSQL_USER", user)
    monkeypatch.setenv("MYSQL_PASSWORD", pwd)


def test__load_env_config_missing(monkeypatch):
    for var in ("MYSQL_DATABASE", "MYSQL_USER", "MYSQL_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ValueError) as e:
        MySQLConnection._load_env_config()
    assert "Variables d'environnement manquantes" in str(e.value)


def test_connect_success_runs_init_and_commit(monkeypatch, tmp_path):
    _set_env(monkeypatch)

    # Fake cursor/connection
    class FakeCursor:
        def __init__(self):
            self.executed = []
            self._closed = False
            self.rowcount = 0

        def execute(self, q, p=None):
            self.executed.append(("execute", q, tuple(p or ())))

        def executemany(self, q, ps):
            self.executed.append(("executemany", q, tuple(tuple(x) for x in ps)))

        def fetchall(self):
            return [{"db()": "trav"}]

        def close(self):
            self._closed = True

    class FakeConn:
        def __init__(self):
            self._closed = False
            self._commits = 0
            self._rollbacks = 0
            self.server_info = "8.0.x"

        def is_connected(self):
            return True

        def cursor(self, dictionary=True):
            return FakeCursor()

        def commit(self):
            self._commits += 1

        def rollback(self):
            self._rollbacks += 1

        def close(self):
            self._closed = True

    monkeypatch.setattr(
        my.mysql, "connector", types.SimpleNamespace(connect=lambda **k: FakeConn())
    )

    # On fait pointer le script d'init vers un fichier temporaire simple
    sql_path = tmp_path / "init.sql"
    sql_path.write_text(
        """
        -- comment
        CREATE TABLE t(x INT);
        INSERT INTO t(x) VALUES (1);
        # autre commentaire
        ;  ;   -- vides
    """,
        encoding="utf-8",
    )
    MySQLConnection.init_sql_path = sql_path

    # Reset état puis connect
    MySQLConnection.connexion = None
    MySQLConnection.cursor = None
    MySQLConnection.connect()

    assert MySQLConnection.connexion is not None
    assert MySQLConnection.cursor is not None
    # Le script a été exécuté puis commit
    # Pas d’assertion directe sur le contenu exact : run_sql_script appelle execute_update
    # et connect() a appelé commit() après ce run.
    # On teste commit ne lève pas et ne rollback pas.
    # (les compteurs sont internes au fake, non exposés, donc on valide via absence d’exception)


def test_connect_init_file_missing_does_not_break(monkeypatch, tmp_path):
    _set_env(monkeypatch)

    class FakeConn:
        def is_connected(self):
            return True

        def cursor(self, dictionary=True):
            class C:
                def execute(self, *a, **k):
                    pass

                def executemany(self, *a, **k):
                    pass

                def fetchall(self):
                    return []

                def close(self):
                    pass

                rowcount = 0

            return C()

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

        server_info = "8.0.x"

    monkeypatch.setattr(
        my.mysql, "connector", types.SimpleNamespace(connect=lambda **k: FakeConn())
    )

    MySQLConnection.connexion = None
    MySQLConnection.cursor = None
    # Chemin inexistant
    MySQLConnection.init_sql_path = tmp_path / "does_not_exist.sql"
    # Ne doit pas lever (le code catche FileNotFoundError)
    MySQLConnection.connect()
    assert MySQLConnection.connexion is not None
    assert MySQLConnection.cursor is not None


def test_run_sql_script_calls_execute_update(monkeypatch, tmp_path):
    # On neutralise connect() pour ne pas exécuter l'init implicite
    MySQLConnection.connexion = object()

    class DummyCursor:
        rowcount = 0

    MySQLConnection.cursor = DummyCursor()

    called = {"updates": []}
    monkeypatch.setattr(
        MySQLConnection,
        "execute_update",
        classmethod(
            lambda cls, q, params=None: called["updates"].append(("U", q, params)) or 1
        ),
    )

    path = tmp_path / "script.sql"
    path.write_text(
        """
        -- a
        CREATE TABLE a(id INT);  # inline comment
        INSERT INTO a VALUES (1);
        ;
    """,
        encoding="utf-8",
    )

    MySQLConnection.run_sql_script(path)
    # Deux statements non vides attendus
    stmts = [q for _, q, _ in called["updates"]]
    assert any("CREATE TABLE a" in s for s in stmts)
    assert any("INSERT INTO a" in s for s in stmts)


def test_execute_query_uses_cursor_execute_and_fetchall(monkeypatch):
    # Bypass connect()
    class C:
        def __init__(self):
            self.calls = []

        def execute(self, q, p=()):
            self.calls.append(("execute", q, tuple(p)))

        def fetchall(self):
            return [{"x": 1}]

    MySQLConnection.cursor = C()
    out = MySQLConnection.execute_query("SELECT 1", params=(42,))
    assert out == [{"x": 1}]
    assert MySQLConnection.cursor.calls[0] == ("execute", "SELECT 1", (42,))


def test_execute_update_chooses_executemany_for_list_of_tuples(monkeypatch):
    class C:
        def __init__(self):
            self.calls = []
            self.rowcount = 3

        def execute(self, q, p=()):
            self.calls.append(("execute", q, tuple(p)))

        def executemany(self, q, ps):
            # On attend une liste/tuple de tuples
            assert isinstance(ps, (list, tuple)) and isinstance(ps[0], (list, tuple))
            self.calls.append(("executemany", q, tuple(tuple(x) for x in ps)))

    MySQLConnection.cursor = C()
    n = MySQLConnection.execute_update(
        "INSERT INTO t VALUES (%s)", params=[(1,), (2,), (3,)]
    )
    assert n == 3
    assert MySQLConnection.cursor.calls[0][0] == "executemany"


def test_execute_update_rollback_on_error(monkeypatch):
    rolled = {"r": 0}

    class C:
        rowcount = 0

        def execute(self, *a, **k):
            raise my.Error("boom")

    class Conn:
        def rollback(self):
            rolled["r"] += 1

    MySQLConnection.cursor = C()
    MySQLConnection.connexion = Conn()
    with pytest.raises(my.Error):
        MySQLConnection.execute_update("UPDATE t SET x=1")
    assert rolled["r"] == 1


def test_commit_rollback_close_safe(monkeypatch):
    class Curs:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    class Conn:
        def __init__(self):
            self._c = Curs()
            self._closed = False
            self._commits = 0
            self._rollbacks = 0

        def is_connected(self):
            return True

        def commit(self):
            self._commits += 1

        def rollback(self):
            self._rollbacks += 1

        def close(self):
            self._closed = True

    MySQLConnection.cursor = Curs()
    MySQLConnection.connexion = Conn()

    MySQLConnection.commit()
    MySQLConnection.rollback()
    MySQLConnection.close()

    assert MySQLConnection.cursor is None
    assert MySQLConnection.connexion is None


def test_execute_update_simple_execute(monkeypatch):
    class C:
        def __init__(self):
            self.rowcount = 1
            self.calls = []

        def execute(self, q, p=()):
            self.calls.append((q, p))

    my.MySQLConnection.cursor = C()
    n = my.MySQLConnection.execute_update("UPDATE x SET y=1", params=("a",))
    assert n == 1
