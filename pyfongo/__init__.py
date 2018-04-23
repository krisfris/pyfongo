import os
import json
import shutil
from bson import ObjectId, json_util
from collections import defaultdict, namedtuple

InsertOneResult = namedtuple('InsertOneResult', ['inserted_id'])
InsertManyResult = namedtuple('InsertManyResult', ['inserted_ids'])

def _project(doc, projection):
    """Return new doc with items filtered according to projection."""
    def _include_key(key, projection):
        for k, v in projection.items():
            if key == k:
                if v == 0:
                    return False
                elif v == 1:
                    return True
                else:
                    raise ValueError('Projection value must be 0 or 1.')
        if projection and key != '_id':
            return False
        return True
    return {k: v for k, v in doc.items() if _include_key(k, projection)}

def _match(doc, query):
    """Decide whether doc matches query."""
    for k, v in query.items():
        if doc.get(k, object()) != v:
            return False
    return True

class Collection:
    def __init__(self, path):
        self._path = path
        os.makedirs(path, exist_ok=True)

    def _iter_col(self):
        for filename in os.listdir(self._path):
            path = os.path.join(self._path, filename)
            with open(path) as f:
                docs = json_util.loads(f.read())
            yield from docs

    def find(self, query={}, projection={}):
        for doc in self._iter_col():
            if _match(doc, query):
                yield _project(doc, projection)

    def find_one(self, query={}, projection={}):
        try:
            return next(self.find(query, projection))
        except StopIteration:
            return None

    def insert_one(self, doc):
        if '_id' not in doc:
            doc['_id'] = ObjectId()

        # Create new file for now, TODO change this later
        path = os.path.join(self._path, str(doc['_id']) + '.json')
        with open(path, 'w') as f:
            f.write(json_util.dumps([doc]))

        return InsertOneResult(doc['_id'])

    def insert_many(self, docs):
        for doc in docs:
            if '_id' not in doc:
                doc['_id'] = ObjectId()

        # Create new file for now, TODO change this later
        path = os.path.join(self._path, str(doc[0]['_id']) + '.json')
        with open(path, 'w') as f:
            f.write(json_util.dumps(docs))

        return InsertManyResult([doc['_id'] for doc in docs])

    def update_one(self, query, update):
        for filename in os.listdir(self._path):
            path = os.path.join(self._path, filename)
            with open(path) as f:
                docs = json_util.loads(f.read())
            for doc in docs:
                if _match(doc, query):
                    for k, v in update['$set'].items():
                        doc[k] = v
                    with open(path, 'w') as f:
                        f.write(json_util.dumps(docs))
                    return # TODO return correct value
        return # TODO return correct value

    def update_many(self, query, doc):
        for filename in os.listdir(self._path):
            path = os.path.join(self._path, filename)
            with open(path) as f:
                docs = json_util.loads(f.read())
            matched = False
            for doc in docs:
                if _match(doc, query):
                    matched = True
                    for k, v in update['$set'].items():
                        doc[k] = v
            if matched:
                with open(path, 'w') as f:
                    f.write(json_util.dumps(docs))
        return # TODO return correct value

    def delete_one(self, query):
        for filename in os.listdir(self._path):
            path = os.path.join(self._path, filename)
            with open(path) as f:
                docs = json_util.loads(f.read())
            new_docs = []
            matched_count = 0
            for doc in docs:
                if _match(doc, query) and matched_count == 0:
                    matched_count += 1
                    continue
                else:
                    new_docs.append(doc)
            if matched_count > 0:    
                with open(path, 'w') as f:
                    f.write(json_util.dumps(new_docs))
                return # TODO return correct value
        return # TODO return correct value

    def delete_many(self, query):
        for filename in os.listdir(self._path):
            path = os.path.join(self._path, filename)
            with open(path) as f:
                docs = json_util.loads(f.read())
            docs = [x for x in docs if not _match(x, query)]
            with open(path, 'w') as f:
                f.write(json_util.dumps(docs))
        return # TODO return correct value

class Database:
    def __init__(self, path):
        self._path = path
        os.makedirs(path, exist_ok=True)

    def __getattr__(self, attr):
        return Collection(os.path.join(self._path, attr))

    def collection_names(self):
        return os.listdir(self._path)

    __getitem__ = __getattr__

class FongoClient:
    def __init__(self, path):
        self._path = path

    def __getattr__(self, attr):
        return Database(os.path.join(self._path, attr))

    __getitem__ = __getattr__

    def database_names(self):
        return os.listdir(self._path)

    def drop_database(self, name):
        shutil.rmtree(os.path.join(self._path, name))

class PyFongo:
    """This class is for flask apps that use flask_pymongo."""
    def init_app(self, app):
        self._cx = FongoClient(app.config['MONGO_PATH'])
        self._db = self._cx[app.config['MONGO_DBNAME']]

    @property
    def cx(self):
        return self._cx

    @property
    def db(self):
        return self._db

if __name__ == '__main__':
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        print('using tmpdir', tmpdir)

        class App:
            config = dict(MONGO_DBNAME='hello', MONGO_PATH=tmpdir)

        mongo = PyFongo()
        mongo.init_app(App())

        r = mongo.db.dataset_data.insert_one({'hello': 'world'})
        r = mongo.db.dataset_data.insert_one({'hello': 'peter'})
        r = mongo.db.dataset_data.find_one()

        print(r)
