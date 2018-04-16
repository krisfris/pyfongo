import os
import tempfile
import random
import pytest

from pyfongo import MongoClient

@pytest.fixture
def cx():
    return MongoClient()

@pytest.fixture()
def cleandir():
    cwd = os.getcwd()
    newpath = tempfile.mkdtemp()
    os.chdir(newpath)
    yield
    os.chdir(cwd)

@pytest.fixture
def filepath(cleandir):
    return str(random.randint(10**5, 10**10))
