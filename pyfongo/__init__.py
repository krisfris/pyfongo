import os
import shutil
from bson import ObjectId, json_util
from collections import namedtuple
from operator import itemgetter
from itertools import islice
from atomicwrites import atomic_write

from pymongo import ASCENDING, DESCENDING, errors  # noqa

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


def _iter_docs(col, query, projection, sort, skip, limit):
    docs = (_project(x, projection) for x in col._iter_col()
            if _match(x, query))

    # Apply sort
    if sort is not None:
        s = list(docs)
        for key, direction in reversed(sort):
            s = sorted(s, key=itemgetter(key),
                       reverse=True if direction == -1 else False)
        docs = iter(s)

    # Apply skip and limit
    docs = islice(docs, skip, (skip+limit) if limit else None)

    return docs


class Cursor:
    def __init__(self, collection, query={}, projection={}, sort=None,
                 skip=0, limit=0):
        self._col = collection
        self._query = query
        self._projection = projection
        self._sort = sort
        self._skip = skip
        self._limit = limit

        self._docs = None

    def _execute(self):
        self._docs = _iter_docs(self._col, self._query, self._projection,
                                self._sort, self._skip, self._limit)

    def _check_okay_to_chain(self):
        if self._docs is not None:
            raise errors.InvalidOperation('cannot set options after executing query')

    def __iter__(self):
        return self

    def __next__(self):
        if self._docs is None:
            self._execute()
        return next(self._docs)

    def sort(self, key_or_list, direction=None):
        """Sorts this cursor's results.

        Takes either a single key and a direction, or a list of (key,
        direction) pairs. The key(s) must be an instance of ``(str,
        unicode)``, and the direction(s) must be one of
        (:data:`~pymongo.ASCENDING`,
        :data:`~pymongo.DESCENDING`). Raises
        :class:`~pymongo.errors.InvalidOperation` if this cursor has
        already been used. Only the last :meth:`sort` applied to this
        cursor has any effect.
        """
        self._check_okay_to_chain()
        if isinstance(key_or_list, str):
            if direction is None:
                direction = 1
            self._sort = [(key_or_list, direction)]
        elif isinstance(key_or_list, list):
            self._sort = key_or_list
        else:
            raise TypeError('key_or_list has invalid type')
        return self

    def skip(self, n):
        """Skips the first `n` results of this cursor.

        Raises TypeError if skip is not an instance of int. Raises
        InvalidOperation if this cursor has already been used. The last `n`
        applied to this cursor takes precedence.
        """
        if not isinstance(n, int):
            raise TypeError('skip must be an int')
        self._check_okay_to_chain()

        self._skip = n
        return self

    def limit(self, n):
        """Limits the number of results to be returned by this cursor.

        Raises TypeError if limit is not an instance of int. Raises
        InvalidOperation if this cursor has already been used. The
        last `n` applied to this cursor takes precedence. A limit
        of ``0`` is equivalent to no limit.
        """
        if not isinstance(n, int):
            raise TypeError('n must be an int')
        self._check_okay_to_chain()

        self._limit = n
        return self

    def count(self, with_limit_and_skip=False):
        """Get the size of the results set for this query.

        Returns the number of documents in the results set for this query. Does
        not take :meth:`limit` and :meth:`skip` into account by default - set
        `with_limit_and_skip` to ``True`` if that is the desired behavior.
        """
        if with_limit_and_skip:
            docs = _iter_docs(self._col, self._query, self._projection,
                              None, self._skip, self._limit)
        else:
            docs = _iter_docs(self._col, self._query, self._projection,
                              None, None, None)
        return sum(1 for _ in docs)


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
        return Cursor(self, query, projection)

    def find_one(self, query={}, projection={}):
        try:
            return next(self.find(query, projection))
        except StopIteration:
            return None

    def distinct(self, key):
        values = set()
        for doc in self.find():
            if key in doc:
                values.add(doc[key])
        return list(values)

    def insert_one(self, doc):
        if '_id' not in doc:
            doc['_id'] = ObjectId()

        # Create new file for now, TODO change this later
        path = os.path.join(self._path, str(doc['_id']) + '.json')
        with atomic_write(path) as f:
            f.write(json_util.dumps([doc]))

        return InsertOneResult(doc['_id'])

    def insert_many(self, docs):
        for doc in docs:
            if '_id' not in doc:
                doc['_id'] = ObjectId()

        # Create new file for now, TODO change this later
        path = os.path.join(self._path, str(docs[0]['_id']) + '.json')
        with atomic_write(path) as f:
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
                    with atomic_write(path, overwrite=True) as f:
                        f.write(json_util.dumps(docs))
                    return  # TODO return correct value
        return  # TODO return correct value

    def update_many(self, query, update):
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
                with atomic_write(path, overwrite=True) as f:
                    f.write(json_util.dumps(docs))
        return  # TODO return correct value

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
                with atomic_write(path, overwrite=True) as f:
                    f.write(json_util.dumps(new_docs))
                return  # TODO return correct value
        return  # TODO return correct value

    def delete_many(self, query):
        for filename in os.listdir(self._path):
            path = os.path.join(self._path, filename)
            with open(path) as f:
                docs = json_util.loads(f.read())
            docs = [x for x in docs if not _match(x, query)]
            with atomic_write(path, overwrite=True) as f:
                f.write(json_util.dumps(docs))
        return  # TODO return correct value


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
        self._cx = FongoClient(app.config['FONGO_PATH'])
        self._db = self._cx[app.config['FONGO_DBNAME']]

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
            config = dict(FONGO_DBNAME='hello', FONGO_PATH=tmpdir)

        fongo = PyFongo()
        fongo.init_app(App())

        r = fongo.db.dataset_data.insert_one({'hello': 'world'})
        r = fongo.db.dataset_data.insert_one({'hello': 'peter'})
        r = fongo.db.dataset_data.find_one()

        print(r)
