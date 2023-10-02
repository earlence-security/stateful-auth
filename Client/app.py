import os
import sys
from flask import Flask, url_for, session, request, send_file
from flask import render_template, redirect
from utils import build_policy_decription_dict 
import requests
import json

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

policy_dict=build_policy_decription_dict()

@app.route('/')
def homepage():
    token = session.get('token')
    return render_template('home.html', token=token)


@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'GET':
        return render_template('login.html', policy_dict=policy_dict)
    
    selected_option = request.form.get('selected_option')
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

@app.route('/policy/<policy_hash>')
def send_policy(policy_hash):

    curr_dir = os.path.abspath(os.path.dirname(__file__))
    auth_lib_dir = os.path.join(curr_dir, 'policies')
    file_path = os.path.join(auth_lib_dir, policy_hash)

    return send_file(file_path)

@app.route('/make_request', methods=['GET', 'POST'])
def make_request():
    token = session.get('token')
    policy = policy_dict[token["policy"]]
    result = ""
    if request.method == 'POST':
        selected_api = request.form.get('api_option')
        selected_method = request.form.get('method_option')
        input_api_append = request.form.get('api_append')
        target_api = selected_api
        if not input_api_append == "":
            target_api = os.path.join(selected_api, input_api_append)
        headers = {
            'Authorization': f'Bearer {token["access_token"]}',
        }

        try:
            if selected_method == 'GET':
                response = requests.get(target_api, headers=headers)

            if selected_method == 'POST':
                headers = {
                    'Authorization': f'Bearer {token["access_token"]}',
                    'Content-Type': 'application/json',
                }
                request_body = request.form.get('request_body')
                response = requests.post(target_api, headers=headers, data=request_body) 

            if selected_method == 'DELETE':
                response = requests.delete(target_api, headers=headers)

            if response.status_code !=  403:
                response.raise_for_status()

            if response.text != "":
                json_object = json.loads(response.content)
                result = json.dumps(json_object, indent=2)

        except Exception as e:
            result = {'error': str(e)}

    return render_template('select_api.html', token=token, policy=policy, result=result)