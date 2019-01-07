# coding: utf-8
from flask import current_app
from werkzeug.contrib.cache import FileSystemCache

cache = None


def init_cache(app):
    global cache
    with app.app_context():
        cache = FileSystemCache(current_app.config['CACHE_DIR'])
