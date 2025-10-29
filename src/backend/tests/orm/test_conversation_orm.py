import pytest
from types import SimpleNamespace
from bson import ObjectId
from bson.errors import InvalidId

import orm.conversation_orm as repo

COL = repo.ConversationOrm.COLLECTION_NAME


@pytest.fixture(autouse=True)
def patch_mongo(monkeypatch):
    """
    Remplace toutes les méthodes de MongoDBConnection utilisées par ConversationRepository
    par des fakes contrôlables.
    """
    calls = {}

    # fake for find_one
    def fake_find_one(collection, query):
        calls.setdefault("find_one", []).append((collection, query))
        # return a sample doc if _id present
        if "_id" in query:
            return {"_id": query["_id"], "title": "hello", "lang639-2": "en"}
        return None

    # fake collection + cursor for find().skip().limit()
    class FakeCursor:
        def __init__(self, docs):
            self._docs = docs
            self._skip = 0
            self._limit = None

        def skip(self, n):
            self._skip = n
            return self

        def limit(self, n):
            self._limit = n
            return self

        def __iter__(self):
            if self._limit is None:
                return iter(self._docs[self._skip :])
            return iter(self._docs[self._skip : self._skip + self._limit])

    class FakeCollection:
        def __init__(self, docs):
            self._docs = docs

        def find(self):
            return FakeCursor(list(self._docs))

    def fake_get_collection(collection):
        calls.setdefault("get_collection", []).append((collection,))
        # return 3 fake docs
        docs = [
            {"_id": ObjectId(), "title": "a", "lang639-2": "en"},
            {"_id": ObjectId(), "title": "b", "lang639-2": "fr"},
            {"_id": ObjectId(), "title": "c", "lang639-2": "en"},
        ]
        return FakeCollection(docs)

    def fake_find(collection, query, limit=100):
        calls.setdefault("find", []).append((collection, query, limit))
        # return docs filtered by query
        key, value = next(iter(query.items()))
        return [
            d
            for d in [
                {"_id": ObjectId(), "title": "a", "lang639-2": "en"},
                {"_id": ObjectId(), "title": "b", "lang639-2": "fr"},
                {"_id": ObjectId(), "title": "c", "lang639-2": "en"},
            ]
            if d.get(key) == value
        ][:limit]

    class InsertOneResult:
        def __init__(self, inserted_id):
            self.inserted_id = inserted_id

    def fake_insert_one(collection, doc):
        calls.setdefault("insert_one", []).append((collection, doc))
        return InsertOneResult(ObjectId())

    class UpdateResult:
        def __init__(self, modified_count):
            self.modified_count = modified_count

    def fake_update_one(collection, filter_q, update_data):
        calls.setdefault("update_one", []).append((collection, filter_q, update_data))
        # simulate 1 mod if filter contains valid ObjectId
        return UpdateResult(1)

    class DeleteResult:
        def __init__(self, deleted_count):
            self.deleted_count = deleted_count

    def fake_delete_one(collection, filter_q):
        calls.setdefault("delete_one", []).append((collection, filter_q))
        return DeleteResult(1)

    def fake_count_documents(collection, filter_q=None):
        calls.setdefault("count_documents", []).append((collection, filter_q))
        if not filter_q:
            return 123
        # if counting by lang
        key, value = next(iter(filter_q.items()))
        if key == "lang639-2":
            return 42 if value == "en" else 1
        return 0

    def fake_aggregate(collection, pipeline):
        calls.setdefault("aggregate", []).append((collection, tuple(pipeline)))
        # return a fake aggregation result
        return [{"lang_code": "en", "count": 10}, {"lang_code": "fr", "count": 3}]

    # apply monkeypatches
    monkeypatch.setattr(
        repo,
        "MongoDBConnection",
        SimpleNamespace(
            find_one=fake_find_one,
            get_collection=fake_get_collection,
            find=fake_find,
            insert_one=fake_insert_one,
            update_one=fake_update_one,
            delete_one=fake_delete_one,
            count_documents=fake_count_documents,
            aggregate=fake_aggregate,
        ),
    )

    return calls


def test_find_by_id_valid(patch_mongo):
    # create a valid ObjectId string
    oid = str(ObjectId())
    res = repo.ConversationRepository.find_by_id(oid)
    assert res is not None
    assert res.get("title") == "hello"


def test_find_by_id_invalid_returns_none(patch_mongo):
    # invalid ObjectId string should be caught and return None
    res = repo.ConversationRepository.find_by_id("not_an_oid")
    assert res is None


def test_find_all_uses_get_collection_and_pagination(patch_mongo):
    out = repo.ConversationRepository.find_all(limit=2, skip=1)
    assert isinstance(out, list)
    assert len(out) == 2 or len(out) <= 2  # ensure limit honored at most 2


def test_find_by_lang_lowercases(patch_mongo):
    res = repo.ConversationRepository.find_by_lang("EN", limit=5)
    # fake_find compares exact value so repository lowercases before calling
    assert isinstance(res, list)
    # results should be filtered to lang 'en' only
    for r in res:
        assert r.get("lang639-2") == "en"


def test_create_returns_string_id(patch_mongo):
    payload = {"title": "new"}
    new_id = repo.ConversationRepository.create(payload)
    assert isinstance(new_id, str)
    # ensure returned id can be parsed into ObjectId
    ObjectId(new_id)


def test_update_valid_id_returns_modified_count(patch_mongo):
    oid = str(ObjectId())
    modified = repo.ConversationRepository.update(oid, {"$set": {"title": "x"}})
    assert isinstance(modified, int)
    assert modified == 1


def test_update_invalid_id_returns_zero(patch_mongo):
    modified = repo.ConversationRepository.update("bad-id", {"$set": {"title": "x"}})
    assert modified == 0


def test_delete_valid_id_returns_deleted_count(patch_mongo):
    oid = str(ObjectId())
    deleted = repo.ConversationRepository.delete(oid)
    assert deleted == 1


def test_delete_invalid_id_returns_zero(patch_mongo):
    deleted = repo.ConversationRepository.delete("bad-id")
    assert deleted == 0


def test_count_all_and_by_lang(patch_mongo):
    total = repo.ConversationRepository.count_all()
    by_lang = repo.ConversationRepository.count_by_lang("EN")
    assert isinstance(total, int) and total == 123
    assert isinstance(by_lang, int) and by_lang == 42


def test_search_by_field(patch_mongo):
    results = repo.ConversationRepository.search_by_field("title", "a", limit=5)
    assert isinstance(results, list)


def test_aggregate_by_lang(patch_mongo):
    agg = repo.ConversationRepository.aggregate_by_lang()
    assert isinstance(agg, list)
    assert agg and "lang_code" in agg[0] and "count" in agg[0]
