import json
from blinker import signal
from bson import ObjectId, json_util
from collections import defaultdict, namedtuple

InsertOneResult = namedtuple('InsertOneResult', ['inserted_id'])

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
    def __init__(self):
        self._documents = []

    def find(self, query={}, projection={}):
        for doc in self._documents:
            if _match(doc, query):
                yield _project(doc, projection)

    def find_one(self, query={}, projection={}):
        for doc in self._documents:
            if _match(doc, query):
                return _project(doc, projection)
        return None

    def insert_one(self, doc):
        if '_id' not in doc:
            doc['_id'] = ObjectId()
        self._documents.append(doc)
        signal('data-changed').send()
        return InsertOneResult(doc['_id'])

    def update_one(self, query, update):
        doc = self.find_one(query)
        if not doc:
            return
        for k, v in update['$set'].items():
            doc[k] = v
        for i, x in enumerate(self._documents):
            if x['_id'] == doc['_id']:
                self._documents[i] = doc
        signal('data-changed').send()

    def update_many(self, query, doc):
        pass

    def delete_one(self, query):
        pass

    def delete_many(self, query):
        pass

class Database:
    def __init__(self):
        self._collections = defaultdict(Collection)

    def __getattr__(self, attr):
        return self._collections[attr]

    __getitem__ = __getattr__

class MongoClient:
    def __init__(self, autosave=False, path=None):
        self.path = path
        self.autosave = autosave

        if autosave:
            signal('data-changed').connect(self._data_changed)

        if path:
            try:
                self.load()
            except FileNotFoundError:
                pass
        else:
            self.reset()

    def __getattr__(self, attr):
        return self._databases[attr]

    __getitem__ = __getattr__

    def _data_changed(self, sender):
        self.save()

    def reset(self):
        self._databases = defaultdict(Database)

    def database_names(self):
        return list(self._databases.keys())

    def save(self):
        data = {'databases': {}}
        for db_name, db in self._databases.items():
            data['databases'][db_name] = {'collections': {}}
            for col_name, col in db._collections.items():
                data['databases'][db_name]['collections'][col_name] = {}
                data['databases'][db_name]['collections'][col_name]['documents'] = col._documents
        open(self.path, 'w').write(json_util.dumps(data))

    def load(self):
        self.reset()
        data = json_util.loads(open(self.path).read())
        for db_name, db in data['databases'].items():
            for col_name, col in db['collections'].items():
                self[db_name][col_name]._documents = col['documents']

class PyMongo:
    """This class is for flask apps that use flask_pymongo."""
    def init_app(self, app):
        self._cx = MongoClient()
        self._db = self._cx[app.config['MONGO_DBNAME']]

    @property
    def cx(self):
        return self._cx

    @property
    def db(self):
        return self._db

if __name__ == '__main__':
    class App:
        config = dict(MONGO_DBNAME='hello')
    mongo = PyMongo()
    mongo.init_app(App())
    r = mongo.db.dataset_data.insert_one({'hello': 'world'})
    r = mongo.db.dataset_data.insert_one({'hello': 'peter'})
    r = mongo.db.dataset_data.find_one()
    print(r)
