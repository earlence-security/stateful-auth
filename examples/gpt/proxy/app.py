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

from .models import db
from .oauth2 import config_oauth
from .auth_routes import auth_bp
from .resource_routes import resource_bp

from flask import Flask, url_for, session, request, send_file
from flask import render_template, redirect
import requests
import json

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv, set_key, find_dotenv
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

from flask import Flask, url_for, session, request, send_file
from flask import render_template, redirect
import requests
import json

from authlib.integrations.flask_client import OAuth

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
    app.register_blueprint(resource_bp, url_prefix="/api")
    return app


app = get_app()

oauth = OAuth(app)
oauth.register(
    name='testClient',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    client_kwargs={
        'scope': 'https://www.googleapis.com/auth/gmail.readonly'
    }
)

@app.route('/get-goog-token', methods=('GET', 'POST'))
def login():
    redirect_uri = url_for('auth', _external=True)
    print(redirect_uri)
    return oauth.testClient.authorize_redirect(redirect_uri)


@app.route('/auth-goog')
def auth():
    token = oauth.testClient.authorize_access_token()
    session['token'] = token
    set_key(dotenv_path=find_dotenv(), key_to_set="goog_tok", value_to_set=token["access_token"])
    return redirect('/')


@app.route('/pop-goog-token')
def poptoken():
    session.pop('token', None)
    return redirect('/')

