
def test_update_one(cx):
    doc = {'hello': 'world'}
    _id = cx.mydb.mycol.insert_one(doc).inserted_id
    cx.mydb.mycol.update_one({'_id': _id}, {'$set': {'hello': 'friend'}})
    assert cx.mydb.mycol.find_one()['hello'] == 'friend'
