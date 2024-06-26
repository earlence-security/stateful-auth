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

parent_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(os.path.join(parent_dir, os.pardir))
parent_dir = os.path.abspath(os.path.join(parent_dir, os.pardir))
auth_lib_dir = os.path.join(parent_dir, 'auth-lib')
history_lib_dir = os.path.join(parent_dir, 'historylib')
sys.path.append(auth_lib_dir)
sys.path.append(parent_dir)

from proxy.app import get_app

from flask import Flask, url_for, session, request, send_file
from flask import render_template, redirect

from authlib.integrations.flask_client import OAuth

from dotenv import load_dotenv, set_key, find_dotenv
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

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
