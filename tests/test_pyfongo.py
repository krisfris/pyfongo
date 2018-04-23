import pytest
import pyfongo

@pytest.fixture(autouse=True)
def populate_db(db):
    docs = [{'hello': 'alice', 'n': 10}, {'hello': 'bob', 'n': 20}]
    db.col.insert_many(docs)

def test_update_one(db):
    db.col.update_one({'hello': 'bob'}, {'$set': {'hello': 'friend'}})
    assert db.col.find_one({'hello': 'friend'})

def test_sort(db):
    docs = list(db.col.find().sort([('hello', -1), ('n', 1)]))
    assert docs[0]['hello'] == 'bob'

def test_sort_after_retrieve(db):
    cursor = db.col.find()
    doc = next(cursor)
    with pytest.raises(pyfongo.errors.InvalidOperation):
        cursor.sort('hello')
