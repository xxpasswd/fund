# coding: utf-8
from flask import current_app
from werkzeug.contrib.cache import FileSystemCache

cache = None


def init_cache():
    global cache
    cache = FileSystemCache(current_app.config['CACHE_DIR'])
