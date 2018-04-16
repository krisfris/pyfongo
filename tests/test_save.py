from pyfongo import MongoClient

def test_save_one_doc(filepath):
    cx = MongoClient(path=filepath)
    doc = {'hello': 'world'}
    cx.mydb.mycol.insert_one(doc)
    cx.save()
    cx = MongoClient(path=filepath)
    assert cx.mydb.mycol.find_one() == doc

def test_autosave_one_doc(filepath):
    cx = MongoClient(path=filepath, autosave=True)
    doc = {'hello': 'world'}
    cx.mydb.mycol.insert_one(doc)
    cx = MongoClient(path=filepath)
    assert cx.mydb.mycol.find_one() == doc
