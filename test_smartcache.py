from tinydb import TinyDB, where
from tinydb.database import Table
from tinydb.storages import MemoryStorage
import pytest

from tinydb_smartcache import SmartCacheTable


@pytest.fixture
def db_smartcache():
    TinyDB.table_class = SmartCacheTable

    db_ = TinyDB(storage=MemoryStorage)
    table = db_.table('_default')

    table.insert_multiple({'int': 1, 'char': c} for c in 'abc')
    return table


@pytest.fixture
def db():
    db_ = TinyDB(storage=MemoryStorage)
    db_.drop_tables()

    db_.insert_multiple({'int': 1, 'char': c} for c in 'abc')
    return db_


def test_smart_query_cache(db_smartcache):
    db = db_smartcache

    query = where('int') == 1
    dummy = where('int') == 2

    assert len(db.search(query)) == 3
    assert len(db.search(dummy)) == 0
    
    assert len(db._query_cache[query]) == 3
    assert len(db._query_cache[dummy]) == 0
    
    db.truncate()
    
    assert not db.search(query)
    assert not db.search(dummy)
    assert len(db._query_cache[query]) == 0
    assert len(db._query_cache[dummy]) == 0

    # Test insert
    db.insert({'int': 1})

    assert len(db._query_cache) == 2
    assert len(db._query_cache[query]) == 1
    assert len(db._query_cache[dummy]) == 0

    # Test update
    db.update({'int': 2}, where('int') == 1)

    assert len(db._query_cache[query]) == 0
    assert len(db._query_cache[dummy]) == 1
    assert db.count(query) == 0

    # Test remove
    db.insert({'int': 1})
    db.remove(where('int') == 1)

    assert db.count(where('int') == 1) == 0


def test_custom_table_class_via_class_attribute(db):
    TinyDB.table_class = SmartCacheTable

    table = db.table('table3')
    assert isinstance(table, SmartCacheTable)

    TinyDB.table_class = Table


# def test_custom_table_class_via_instance_attribute(db):
#     db.table_class = SmartCacheTable
#     table = db.table('table3')
#     assert isinstance(table, SmartCacheTable)


def test_truncate(db_smartcache):
    db = db_smartcache

    db.truncate()

    db.insert({})
    db.truncate()

    assert len(db) == 0


def test_all(db_smartcache):
    db = db_smartcache

    db.truncate()

    for i in range(10):
        db.insert({})

    assert len(db.all()) == 10


def test_insert(db_smartcache):
    db = db_smartcache

    db.truncate()
    db.insert({'int': 1, 'char': 'a'})

    assert db.count(where('int') == 1) == 1

    db.truncate()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    assert db.count(where('int') == 1) == 3
    assert db.count(where('char') == 'a') == 1


def test_insert_ids(db_smartcache):
    db = db_smartcache

    db.truncate()
    assert db.insert({'int': 1, 'char': 'a'}) == 1
    assert db.insert({'int': 1, 'char': 'a'}) == 2


def test_insert_multiple(db_smartcache):
    db = db_smartcache

    db.truncate()
    assert not db.contains(where('int') == 1)

    # Insert multiple from list
    db.insert_multiple([{'int': 1, 'char': 'a'},
                        {'int': 1, 'char': 'b'},
                        {'int': 1, 'char': 'c'}])

    assert db.count(where('int') == 1) == 3
    assert db.count(where('char') == 'a') == 1

    # Insert multiple from generator function
    def generator():
        for j in range(10):
            yield {'int': j}

    db.truncate()

    db.insert_multiple(generator())

    for i in range(10):
        assert db.count(where('int') == i) == 1
    if hasattr(where('int'), 'exists'):
        assert db.count(where('int').exists()) == 10
    else:
        assert db.count(where('int')) == 10

    # Insert multiple from inline generator
    db.truncate()

    db.insert_multiple({'int': i} for i in range(10))

    for i in range(10):
        assert db.count(where('int') == i) == 1


def test_insert_multiple_with_ids(db_smartcache):
    db = db_smartcache

    db.truncate()

    # Insert multiple from list
    assert db.insert_multiple([{'int': 1, 'char': 'a'},
                               {'int': 1, 'char': 'b'},
                               {'int': 1, 'char': 'c'}]) == [1, 2, 3]


def test_remove(db_smartcache):
    db = db_smartcache

    db.remove(where('char') == 'b')

    assert len(db) == 2
    assert db.count(where('int') == 1) == 2


def test_remove_multiple(db_smartcache):
    db = db_smartcache

    db.remove(where('int') == 1)

    assert len(db) == 0


def test_remove_ids(db_smartcache):
    db = db_smartcache

    db.remove(doc_ids=[1, 2])

    assert len(db) == 1


def test_update(db_smartcache):
    db = db_smartcache

    assert db.count(where('int') == 1) == 3

    db.update({'int': 2}, where('char') == 'a')

    assert db.count(where('int') == 2) == 1
    assert db.count(where('int') == 1) == 2


def test_update_transform(db_smartcache):
    db = db_smartcache

    def increment(field):
        def transform(el):
            el[field] += 1
        return transform

    def delete(field):
        def transform(el):
            del el[field]
        return transform

    assert db.count(where('int') == 1) == 3

    db.update(increment('int'), where('char') == 'a')
    db.update(delete('char'), where('char') == 'a')

    assert db.count(where('int') == 2) == 1
    assert db.count(where('char') == 'a') == 0
    assert db.count(where('int') == 1) == 2


def test_update_ids(db_smartcache):
    db = db_smartcache

    db.update({'int': 2}, doc_ids=[1, 2])

    assert db.count(where('int') == 2) == 2


def test_search(db_smartcache):
    db = db_smartcache

    assert not db._query_cache
    assert len(db.search(where('int') == 1)) == 3

    assert len(db._query_cache) == 1
    assert len(db.search(where('int') == 1)) == 3  # Query result from cache


def test_contians(db_smartcache):
    db = db_smartcache

    assert db.contains(where('int') == 1)
    assert not db.contains(where('int') == 0)


def test_contains_id(db_smartcache):
    db = db_smartcache

    assert not db.contains(doc_id=88)


def test_get(db_smartcache):
    db = db_smartcache

    item = db.get(where('char') == 'b')
    assert item['char'] == 'b'


def test_get_ids(db_smartcache):
    db = db_smartcache

    el = db.all()[0]
    assert db.get(doc_id=el.doc_id) == el
    assert db.get(doc_id=float('NaN')) is None


def test_count(db_smartcache):
    db = db_smartcache

    assert db.count(where('int') == 1) == 3
    assert db.count(where('char') == 'd') == 0


def test_contains(db_smartcache):
    db = db_smartcache

    assert db.contains(where('int') == 1)
    assert not db.contains(where('int') == 0)


def test_get_idempotent(db_smartcache):
    db = db_smartcache

    u = db.get(where('int') == 1)
    z = db.get(where('int') == 1)
    assert u == z