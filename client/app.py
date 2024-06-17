import os
import sys
from flask import Flask, url_for, session, request, send_file
from flask import render_template, redirect
from utils import build_policy_decription_dict 
import requests
import json
import time

# add the auth-lib in our directory as path
parent_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.abspath(os.path.join(parent_dir, os.pardir))
auth_lib_dir = os.path.join(parent_dir, 'auth-lib')
history_lib_dir = os.path.join(parent_dir, 'historylib')
sys.path.append(auth_lib_dir)
sys.path.append(parent_dir)

from authlib.integrations.flask_client import OAuth
from historylib.client_utils import get_history, history_to_file, delete_history_file, get_batchhistory, batch_history_to_file
from historylib.batch_history_list import BatchHistoryList

app = Flask(__name__)
app.secret_key = 'secret'
app.config.from_object('config')

oauth = OAuth(app)
oauth.register(
    name='testClient',
    client_id=app.config['CLIENT_ID'],
    client_secret=app.config['CLIENT_SECRET'],
    access_token_url=app.config['ACCESS_TOKEN_URL'],
    access_token_params=None,
    authorize_url=app.config['AUTHORIZE_URL'],
    authorize_params=None,
    client_kwargs=app.config['CLIENT_KWARGS']
)

policy_dict = build_policy_decription_dict()
history_path = app.config['HISTORY_DIRECTORY']
is_macaroon = app.config['MACAROON']
if not os.path.exists(history_path):
   os.makedirs(history_path)

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
    return oauth.testClient.authorize_redirect(app.config['REDIRECT_URI'], 
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
    if not token:
        return redirect('/')
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
        
        if not is_macaroon:
            headers = {
                'Authorization': f'Bearer {token["access_token"]}',
                'Authorization-History': '',
            }

        objs_to_be_accessed=[]
        # get history attached with this obj
        if input_api_append:
            objs_to_be_accessed = [input_api_append]
            obj_history = get_batchhistory(objs_to_be_accessed, history_path, token["access_token"])
            headers['Authorization-History'] = obj_history.to_json()
        
        send_time = 0
        recv_time = 0

        try:
            if selected_method == 'GET':
                send_time = time.time()
                response = requests.get(target_api, headers=headers)
                recv_time = time.time()

            if selected_method == 'POST':
                headers['Content-Type'] = 'application/json'
                request_body = request.form.get('request_body')
                body_json = json.loads(request_body)
                obj_ids = body_json.get('ids')
                if obj_ids:
                    obj_history = get_batchhistory(obj_ids, history_path, token["access_token"])
                    headers['Authorization-History'] = obj_history.to_json()
                send_time = time.time()
                response = requests.post(target_api, headers=headers, data=request_body) 
                recv_time = time.time()

            if selected_method == 'DELETE':
                send_time = time.time()
                response = requests.delete(target_api, headers=headers)
                recv_time = time.time()

                if response.status_code == 204:
                    delete_history_file(input_api_append, history_path)

            if response.status_code !=  403:
                response.raise_for_status()

            if response.text:
                json_object = json.loads(response.content)
                result = json.dumps(json_object, indent=2)
            
            if not is_macaroon:
                # store new history
                new_auth_history = response.headers.get('Set-Authorization-History')
                if new_auth_history:
                    print(response.headers.get('Set-Authorization-History'))
                    resp_hist_list = BatchHistoryList(json_str=response.headers.get('Set-Authorization-History'))
                    batch_history_to_file(resp_hist_list, history_path, token["access_token"])

            # Record e2e latecy
            if send_time != 0 and recv_time != 0:
                result += f"\n\nE2E Latency: {(recv_time - send_time) * 1000} milliseconds"

        except Exception as e:
            result = {'error': str(e)}

    return render_template('select_api.html', token=token, policy=policy, result=result)

@app.route('/gethistory', methods=['POST'])
def return_history():
    token = session.get('token')
    obj_id = request.form.get('api_append')  # Get object id from form
    if not obj_id:
        return "No obj_id provided"
    ret = get_history(obj_id, app.config['HISTORY_DIRECTORY'], token["access_token"])

    json_object = json.loads(ret.to_json())
    result = json.dumps(json_object, indent=2)
    return result