import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'pyfongo',
    version = '0.1.0',
    author = 'Kris',
    author_email = '31852063+krisfris@users.noreply.github.com',
    description = ('Fake in-memory mongodb for python'),
    license = '',
    keywords = '',
    url = '',
    packages=find_packages(),
    long_description=read('README.md'),
    data_files = [('', ['LICENSE', 'README.md'])],
    install_requires = ['blinker', 'pymongo']
)
