import pytest

@pytest.fixture(autouse=True)
def populate_db(db):
    doc = {'hello': 'world'}
    _id = db.col.insert_one(doc).inserted_id

def test_update_one(db):
    db.col.update_one({'hello': 'world'}, {'$set': {'hello': 'friend'}})
    assert db.col.find_one()['hello'] == 'friend'

