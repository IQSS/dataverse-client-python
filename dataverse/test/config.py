import os
from dataverse.settings import BASE_PATH

PICS_OF_CATS_DATASET = {
    "id": "1",
    "title": "This Study is about Pictures of Cats",
    "author": "Peter Bull",
    "description": "In this study we prove there can be pictures of cats.",
}

ATOM_DATASET = os.path.join(BASE_PATH, 'resources', 'atom-entry-study.xml')

EXAMPLE_FILES = [
    os.path.join(BASE_PATH, 'test', '__init__.py'),
    os.path.join(BASE_PATH, 'test', 'config.py'),
]
