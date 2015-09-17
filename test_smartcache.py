from tinydb import TinyDB, where
from tinydb.database import Table
from tinydb.storages import MemoryStorage
from tinydb.utils import catch_warning
import pytest

from tinydb_smartcache import SmartCacheTable


@pytest.fixture
def db_smartcache():
    db_ = TinyDB(storage=MemoryStorage)
    db_.purge_tables()

    db_.table_class = SmartCacheTable
    db_ = db_.table('_default')

    db_.insert_multiple({'int': 1, 'char': c} for c in 'abc')
    return db_


@pytest.fixture
def db():
    db_ = TinyDB(storage=MemoryStorage)
    db_.purge_tables()

    db_.insert_multiple({'int': 1, 'char': c} for c in 'abc')
    return db_


def test_smart_query_cache(db):
    db.table_class = SmartCacheTable
    table = db.table('table3')
    query = where('int') == 1
    dummy = where('int') == 2

    assert not table.search(query)
    assert not table.search(dummy)

    # Test insert
    table.insert({'int': 1})

    assert len(table._query_cache) == 2
    assert len(table._query_cache[query]) == 1

    # Test update
    table.update({'int': 2}, where('int') == 1)

    assert len(table._query_cache[dummy]) == 1
    assert table.count(query) == 0

    # Test remove
    table.insert({'int': 1})
    table.remove(where('int') == 1)

    assert table.count(where('int') == 1) == 0


def test_smart_query_cache_via_kwarg(db):
    # For backwards compatibility
    with pytest.raises(DeprecationWarning):
        with catch_warning(DeprecationWarning):
            table = db.table('table3', smart_cache=True)
            assert isinstance(table, SmartCacheTable)


def test_custom_table_class_via_class_attribute(db):
    TinyDB.table_class = SmartCacheTable

    table = db.table('table3')
    assert isinstance(table, SmartCacheTable)

    TinyDB.table_class = Table


def test_custom_table_class_via_instance_attribute(db):
    db.table_class = SmartCacheTable
    table = db.table('table3')
    assert isinstance(table, SmartCacheTable)



@pytest.mark.parametrize('db', [db_smartcache()])
def test_purge(db):
    db.purge()

    db.insert({})
    db.purge()

    assert len(db) == 0


@pytest.mark.parametrize('db', [db_smartcache()])
def test_all(db):
    db.purge()

    for i in range(10):
        db.insert({})

    assert len(db.all()) == 10


@pytest.mark.parametrize('db', [db_smartcache()])
def test_insert(db):
    db.purge()
    db.insert({'int': 1, 'char': 'a'})

    assert db.count(where('int') == 1) == 1

    db.purge()

    db.insert({'int': 1, 'char': 'a'})
    db.insert({'int': 1, 'char': 'b'})
    db.insert({'int': 1, 'char': 'c'})

    assert db.count(where('int') == 1) == 3
    assert db.count(where('char') == 'a') == 1


@pytest.mark.parametrize('db', [db_smartcache()])
def test_insert_ids(db):
    db.purge()
    assert db.insert({'int': 1, 'char': 'a'}) == 1
    assert db.insert({'int': 1, 'char': 'a'}) == 2


@pytest.mark.parametrize('db', [db_smartcache()])
def test_insert_multiple(db):
    db.purge()
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

    db.purge()

    db.insert_multiple(generator())

    for i in range(10):
        assert db.count(where('int') == i) == 1
    if hasattr(where('int'), 'exists'):
        assert db.count(where('int').exists()) == 10
    else:
        assert db.count(where('int')) == 10

    # Insert multiple from inline generator
    db.purge()

    db.insert_multiple({'int': i} for i in range(10))

    for i in range(10):
        assert db.count(where('int') == i) == 1


@pytest.mark.parametrize('db', [db_smartcache()])
def test_insert_multiple_with_ids(db):
    db.purge()

    # Insert multiple from list
    assert db.insert_multiple([{'int': 1, 'char': 'a'},
                               {'int': 1, 'char': 'b'},
                               {'int': 1, 'char': 'c'}]) == [1, 2, 3]


@pytest.mark.parametrize('db', [db_smartcache()])
def test_remove(db):
    db.remove(where('char') == 'b')

    assert len(db) == 2
    assert db.count(where('int') == 1) == 2


@pytest.mark.parametrize('db', [db_smartcache()])
def test_remove_multiple(db):
    db.remove(where('int') == 1)

    assert len(db) == 0


@pytest.mark.parametrize('db', [db_smartcache()])
def test_remove_ids(db):
    db.remove(eids=[1, 2])

    assert len(db) == 1


@pytest.mark.parametrize('db', [db_smartcache()])
def test_update(db):
    assert db.count(where('int') == 1) == 3

    db.update({'int': 2}, where('char') == 'a')

    assert db.count(where('int') == 2) == 1
    assert db.count(where('int') == 1) == 2


@pytest.mark.parametrize('db', [db_smartcache()])
def test_update_transform(db):
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


@pytest.mark.parametrize('db', [db_smartcache()])
def test_update_ids(db):
    db.update({'int': 2}, eids=[1, 2])

    assert db.count(where('int') == 2) == 2


@pytest.mark.parametrize('db', [db_smartcache()])
def test_search(db):
    assert not db._query_cache
    assert len(db.search(where('int') == 1)) == 3

    assert len(db._query_cache) == 1
    assert len(db.search(where('int') == 1)) == 3  # Query result from cache


@pytest.mark.parametrize('db', [db_smartcache()])
def test_contians(db):
    assert db.contains(where('int') == 1)
    assert not db.contains(where('int') == 0)


@pytest.mark.parametrize('db', [db_smartcache()])
def test_contains_ids(db):
    assert db.contains(eids=[1, 2])
    assert not db.contains(eids=[88])


@pytest.mark.parametrize('db', [db_smartcache()])
def test_get(db):
    item = db.get(where('char') == 'b')
    assert item['char'] == 'b'


@pytest.mark.parametrize('db', [db_smartcache()])
def test_get_ids(db):
    el = db.all()[0]
    assert db.get(eid=el.eid) == el
    assert db.get(eid=float('NaN')) is None


@pytest.mark.parametrize('db', [db_smartcache()])
def test_count(db):
    assert db.count(where('int') == 1) == 3
    assert db.count(where('char') == 'd') == 0


@pytest.mark.parametrize('db', [db_smartcache()])
def test_contains(db):
    assert db.contains(where('int') == 1)
    assert not db.contains(where('int') == 0)


@pytest.mark.parametrize('db', [db_smartcache()])
def test_contains_ids(db):
    assert db.contains(eids=[1, 2])


@pytest.mark.parametrize('db', [db_smartcache()])
def test_get_idempotent(db):
    u = db.get(where('int') == 1)
    z = db.get(where('int') == 1)
    assert u == z
