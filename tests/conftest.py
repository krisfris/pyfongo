import tempfile
import pytest

from pyfongo import FongoClient
from pymongo import MongoClient

@pytest.fixture(params=['pymongo', 'pyfongo'])
def cx(request):
    if request.param == 'pymongo':
        yield MongoClient()
    elif request.param == 'pyfongo':
        with tempfile.TemporaryDirectory() as tmpdir:
            yield FongoClient(tmpdir)
    else:
        raise ValueError('Invalid fixture param.')

@pytest.fixture
def db(cx):
    yield cx.test_pyfongo
    cx.drop_database('test_pyfongo')
