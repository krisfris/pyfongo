import tempfile
import pytest

from pyfongo import FongoClient

@pytest.fixture
def cx():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield FongoClient(tmpdir)
