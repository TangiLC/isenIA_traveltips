import types
import builtins
import pytest

import connexion.mongo_connect as mc

MongoDBConnection = mc.MongoDBConnection


@pytest.fixture(autouse=True)
def no_dotenv(monkeypatch):
    # Neutralise load_dotenv pour éviter de charger un vrai .env
    monkeypatch.setattr(mc, "load_dotenv", lambda: None)


def _set_env(
    monkeypatch, host="localhost", port="27017", db="testdb", user="u", pwd="p"
):
    monkeypatch.setenv("MONGODB_HOST", host)
    monkeypatch.setenv("MONGODB_PORT", port)
    monkeypatch.setenv("MONGO_DATABASE", db)
    monkeypatch.setenv("MONGO_ROOT_USER", user)
    monkeypatch.setenv("MONGO_ROOT_PASSWORD", pwd)


def test__load_env_config_missing_raises(monkeypatch):
    # Manque database, username, password
    for var in ("MONGO_DATABASE", "MONGO_ROOT_USER", "MONGO_ROOT_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ValueError) as e:
        MongoDBConnection._load_env_config()
    assert "Variables d'environnement manquantes" in str(e.value)


def test_connect_success_and_close(monkeypatch):
    _set_env(monkeypatch)

    class FakeAdmin:
        def command(self, cmd):
            assert cmd == "ping"

    class FakeClient:
        def __init__(self, *a, **k):
            self._closed = False

        @property
        def admin(self):
            return FakeAdmin()

        def server_info(self):
            return {"version": "7.0.0"}

        def __getitem__(self, name):
            return {"_db_name": name}

        def close(self):
            self._closed = True

    monkeypatch.setattr(
        mc, "MongoClient", lambda uri, serverSelectionTimeoutMS: FakeClient()
    )
    # Reset état global
    MongoDBConnection.client = None
    MongoDBConnection.db = None

    MongoDBConnection.connect()
    assert MongoDBConnection.client is not None
    assert MongoDBConnection.db == {"_db_name": "testdb"}

    MongoDBConnection.close()
    assert MongoDBConnection.client is None
    assert MongoDBConnection.db is None


def test_connect_connection_failure_rethrows(monkeypatch):
    _set_env(monkeypatch)

    class Boom(mc.ConnectionFailure):
        pass

    class FakeClientBad:
        @property
        def admin(self):
            class A:
                def command(self, cmd):
                    raise Boom("down")

            return A()

    monkeypatch.setattr(mc, "MongoClient", lambda *a, **k: FakeClientBad())
    MongoDBConnection.client = None
    MongoDBConnection.db = None

    with pytest.raises(mc.ConnectionFailure):
        MongoDBConnection.connect()

    assert MongoDBConnection.client is None
    assert MongoDBConnection.db is None


def test_get_collection_triggers_connect(monkeypatch):
    _set_env(monkeypatch)

    called = {"connect": 0}

    def fake_connect():
        called["connect"] += 1
        MongoDBConnection.client = types.SimpleNamespace(
            admin=types.SimpleNamespace(command=lambda _: None),
            server_info=lambda: {"version": "x"},
        )
        MongoDBConnection.db = {"col": "X"}

    monkeypatch.setattr(
        MongoDBConnection, "connect", classmethod(lambda cls: fake_connect())
    )

    MongoDBConnection.client = None
    MongoDBConnection.db = None
    col = MongoDBConnection.get_collection("col")
    assert col == "X"
    assert called["connect"] == 1


def test_find_and_find_one_with_limit_and_projection(monkeypatch):
    _set_env(monkeypatch)

    class FakeCursor:
        def __init__(self, docs):
            self.docs = docs
            self._limit = None

        def limit(self, n):
            self._limit = n
            return self

        def __iter__(self):
            yield from (self.docs[: self._limit] if self._limit else self.docs)

    class FakeCollection:
        def __init__(self):
            self._docs = [{"a": 1}, {"a": 2}, {"a": 3}]

        def find(self, query, projection):
            # vérifie passage des paramètres
            assert query == {"a": {"$gte": 1}}
            assert projection == {"_id": 0}
            return FakeCursor(list(self._docs))

        def find_one(self, query, projection):
            assert projection == {"_id": 0}
            return {"a": 99}

    def fake_get_collection(name):
        assert name == "col"
        return FakeCollection()

    MongoDBConnection.db = object()  # court-circuite connect()
    monkeypatch.setattr(
        MongoDBConnection,
        "get_collection",
        classmethod(lambda cls, n: fake_get_collection(n)),
    )

    out = MongoDBConnection.find("col", {"a": {"$gte": 1}}, {"_id": 0}, limit=2)
    assert out == [{"a": 1}, {"a": 2}]
    one = MongoDBConnection.find_one("col", {"a": 1}, {"_id": 0})
    assert one == {"a": 99}


def test_insert_update_delete_count_aggregate(monkeypatch):
    _set_env(monkeypatch)

    class Res:
        def __init__(self, **k):
            self.__dict__.update(k)

    class FakeCollection:
        def insert_one(self, doc):
            return Res(inserted_id="OID1")

        def insert_many(self, docs):
            return Res(inserted_ids=["OID1", "OID2"])

        def update_one(self, q, u, upsert=False):
            assert upsert is True
            return Res(modified_count=1)

        def update_many(self, q, u, upsert=False):
            return Res(modified_count=2)

        def delete_one(self, q):
            return Res(deleted_count=1)

        def delete_many(self, q):
            return Res(deleted_count=3)

        def count_documents(self, q):
            return 7

        def aggregate(self, pipeline):
            return iter([{"k": 1}])

    MongoDBConnection.db = object()
    monkeypatch.setattr(
        MongoDBConnection,
        "get_collection",
        classmethod(lambda cls, n: FakeCollection()),
    )

    r1 = MongoDBConnection.insert_one("c", {"a": 1})
    assert r1.inserted_id == "OID1"
    r2 = MongoDBConnection.insert_many("c", [{"a": 1}, {"a": 2}])
    assert len(r2.inserted_ids) == 2
    u1 = MongoDBConnection.update_one("c", {}, {"$set": {"x": 1}}, upsert=True)
    assert u1.modified_count == 1
    u2 = MongoDBConnection.update_many("c", {}, {"$set": {"x": 1}})
    assert u2.modified_count == 2
    d1 = MongoDBConnection.delete_one("c", {})
    assert d1.deleted_count == 1
    d2 = MongoDBConnection.delete_many("c", {})
    assert d2.deleted_count == 3
    cnt = MongoDBConnection.count_documents("c", {})
    assert cnt == 7
    agg = MongoDBConnection.aggregate("c", [{"$match": {"a": 1}}])
    assert agg == [{"k": 1}]


def test_operation_failure_bubbles(monkeypatch):
    _set_env(monkeypatch)

    class FakeCollection:
        def find(self, *a, **k):
            raise mc.OperationFailure("bad op")

    MongoDBConnection.db = object()
    monkeypatch.setattr(
        MongoDBConnection,
        "get_collection",
        classmethod(lambda cls, n: FakeCollection()),
    )

    with pytest.raises(mc.OperationFailure):
        MongoDBConnection.find("c", {}, None, 0)


def test_close_when_none_safe():
    mc.MongoDBConnection.client = None
    mc.MongoDBConnection.db = None
    mc.MongoDBConnection.close()
