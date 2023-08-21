import os
import sys
from flask import Flask, url_for, session, request
from flask import render_template, redirect

# add the auth-lib in our directory as path
parent_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(os.path.join(parent_dir, os.pardir))
auth_lib_dir = os.path.join(parent_dir, 'auth-lib')
sys.path.append(auth_lib_dir)

from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = 'secret'
app.config.from_object('config')

oauth = OAuth(app)
oauth.register(
    name='testClient',
    client_id=app.config['CLIENT_ID'],
    client_secret=app.config['CLIENT_SECRET'],
    access_token_url='http://127.0.0.1:5000/oauth/token',
    access_token_params=None,
    authorize_url='http://127.0.0.1:5000/oauth/authorize',
    authorize_params=None,
    client_kwargs=app.config['CLIENT_KWARGS']
)

@app.route('/')
def homepage():
    token = session.get('token')
    return render_template('home.html', token=token)


@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'GET':
        return render_template('login.html', policy_hashes=app.config['CLIENT_KWARGS'].get("policy_hashes"))
    
    selected_option = request.form.get('selected_option')
    print(selected_option)
    redirect_uri = url_for('auth', _external=True)
    return oauth.testClient.authorize_redirect(redirect_uri, 
                                               policy_hash=selected_option)


@app.route('/auth')
def auth():
    token = oauth.testClient.authorize_access_token()
    #TODO
    #Put in database not session
    session['token'] = token
    return redirect('/')


@app.route('/logout')
def logout():
    session.pop('token', None)
    return redirect('/')
