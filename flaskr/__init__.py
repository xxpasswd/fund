# coding: utf-8
import os

from flask import Flask, render_template


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY = 'dev',
        DATABASE = os.path.join(app.instance_path, 'flaskr.sqlite'),
        CACHE_DIR = os.path.join(app.instance_path, 'cache')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import cacher
    cacher.init_cache(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import fund
    app.register_blueprint(fund.bp)
    app.add_url_rule('/', endpoint='index')

    @app.route('/h')
    def hello():
        return render_template('base.html')

    return app
