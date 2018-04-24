# pyfongo

pyfongo is an in-process library that implements a self-contained, serverless, zero-configuration, mongodb database engine with pymongo's interface.

Inspired by pymongo and sqlite.

Written for Python 3.6.

## When to use
- unit testing of apps that use mongodb
- stand-in for mongodb during demos and testing
- as application file format
- data analysis using mongodb queries
- temporary database for reorganizing data
- in embedded systems

## Examples

    >>> import pyfongo
    >>> cx = pyfongo.FongoClient('/path/to/datadir')
    >>> db = cx.test
    >>> db.my_collection.insert_one({'x': 10}).inserted_id
    ObjectId('5aded7ff7aea217b9056e9d0')
    >>> db.my_collection.insert_one({'x': 12}).inserted_id
    ObjectId('5aded8467aea217b9056e9d1')
    >>> db.my_collection.find_one()
    {'x': 10, '_id': ObjectId('5aded7ff7aea217b9056e9d0')}
    >>> for item in db.my_collection.find().sort('x', -1):
    ...     print(item['x'])
    ...
    12
    10

## Testing

The same tests are run against both pyfongo and a local mongodb server
using pymongo to ensure that pyfongo mimics mongodb/pymongo's behavior correctly.

Run the tests with: `pipenv run pytest -sv`

Note that you will need to run `pipenv install --dev` once before you can
run the tests.
