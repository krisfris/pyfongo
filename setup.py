import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


version = '0.1.0'


setup(
    name='pyfongo',
    version=version,
    author='Kris',
    author_email='31852063+krisfris@users.noreply.github.com',
    description=('Serverless self-contained database with pymongo interface'),
    license='MIT',
    keywords='',
    url='https://github.com/krisfris/pyfongo',
    packages=find_packages(exclude=['docs', 'tests']),
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    data_files=[('', ['LICENSE', 'README.md'])],
    install_requires=['pymongo', 'atomicwrites']
)
