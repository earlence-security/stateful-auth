"""Proxy is a helper module for intgerating StatefulAuth with real-wolrd applications.
Simply use `app = get_app()` to get a Flask app with StatefulAuth integrated. Then,
register your own resource server endpoints as blueprints to the app. For example:
```
app = get_app()
app.register_blueprint(my_resource_server_bp, url_prefix="/api")
```
"""
import os
import sys

from flask import Flask

from proxy.models import db
from proxy.oauth2 import config_oauth
from proxy.auth_routes import auth_bp

def get_app():
    cwd = os.getcwd()
    app = create_app({
        'SECRET_KEY': 'secret',
        'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:////{cwd}/db.sqlite',
        'ENABLE_STATEFUL_AUTH': True,
        'UPLOAD_FOLDER': os.path.join(cwd, 'policies'),
    })

    return app


def create_app(config=None):
    app = Flask(__name__)
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)
    setup_app(app)
    return app


def setup_app(app):
    db.init_app(app)
    # Create tables if they do not exist already
    with app.app_context():
        db.create_all()
    config_oauth(app)
    # Register Authorizatin blueprints
    app.register_blueprint(auth_bp, url_prefix='')
    return app


app = get_app()
