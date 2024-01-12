import sys
import json
import flask
import dropbox
import requests

from urllib.parse import urlparse
from flask import Blueprint, jsonify, make_response, request
from dropbox import DropboxOAuth2FlowNoRedirect
from dropbox.exceptions import AuthError
from authlib.integrations.flask_oauth2 import current_token

from proxy.oauth2 import require_oauth_stateful
from proxy.models import db
from historylib.proxy_utils import update_history_proxy

# OAuth2 configurations
DROPBOX_API_BASE_URL = "https://api.dropboxapi.com/2"
DROPBOX_CONTENT_BASE_URL = "https://content.dropboxapi.com/2"
APP_KEY = "y1cak69zw7gbeqc"
APP_SECRET = "joqs0dtj9tbahi4"
# REDIRECT_URI = "http://localhost:5000/oauth2callback"
# SCOPES = ['files.metadata.read', 'files.content.read', 'files.content.write']

# Resource server blueprint. In this integration, all the endpoint will
# further send the request to the real server.
resource_bp = Blueprint('resource', __name__)

# Test endpoint
@resource_bp.route('/me')
@require_oauth_stateful()
def api_me():
    user = current_token.user
    return jsonify(id=user.id, username=user.username)

@resource_bp.route('/files/get_metadata', methods=['GET', 'POST'])
@require_oauth_stateful()
@update_history_proxy(session=db.session)
def get_metadata():
    """Get metadata for a file in the /Apps/Joplin folder."""
    try:
        # body = request.get_json()
        # path = body.get('path')
        # abspath = f"/Apps/JoplinDev{path}"
        # resp = requests.post(f"{DROPBOX_API_BASE_URL}files/get_metadata", data={'path': abspath})
        # if resp.status_code != 200:
        #     raise Exception(f"Get metadata failed: {resp.status_code}")
        # print(f"{resp.headers=}")
        # print(f"{resp.json()=}")
        # flask_resp = flask.Response(resp.content, status=resp.status_code, headers=dict(resp.headers))
        # return flask_resp, [resp.json().get('id')]
        return forward_and_process_response()
    except Exception as e:
        print(e)
        return jsonify({'error': e}), 500


@resource_bp.route('/files/list_folder', methods=['POST'])
@require_oauth_stateful()
@update_history_proxy(session=db.session)
def list_folder():
    """List the content of the /Apps/JoplinDev folder."""
    try:
        return forward_and_process_response()
    except Exception as e:
        print(e)
        return jsonify({'error': e}), 500


@resource_bp.route('/files/list_folder/continue', methods=['POST'])
@require_oauth_stateful()
@update_history_proxy(session=db.session)
def list_folder_continue():
    """List the content of the /Apps/JoplinDev folder."""
    try:
        return forward_and_process_response()
    except Exception as e:
        print(e)
        return jsonify({'error': e}), 500


@resource_bp.route('/files/download', methods=['GET', 'POST'])
@require_oauth_stateful()
@update_history_proxy(session=db.session)
def download_file():
    """Download a file from the /Apps/Joplin folder."""
    try:
        # args = request.headers.get('Dropbox-Api-Arg')
        # args = json.loads(args)
        # path = args['path']
        # abspath = f"/Apps/JoplinDev{path}"
        # print({'Authorization': f"Bearer {flask.current_app.config['DROPBOX_OAUTH2_ACCESS_TOKEN']}",
        #        'Dropbox-API-Arg': f'{{"path": "{abspath}"}}'})
        # resp = requests.get("https://content.dropboxapi.com/2/files/download", 
        #              headers={'Authorization': f"Bearer {flask.current_app.config['DROPBOX_OAUTH2_ACCESS_TOKEN']}",
        #                       'Dropbox-API-Arg': f'{{"path": "{abspath}"}}'})
        # if resp.status_code != 200:
        #     raise Exception(f"Download file failed: {resp.status_code}")
        # headers = dict(resp.headers)
        # parsed_api_result = json.loads(headers.get('Dropbox-Api-Result'))
        # headers['Dropbox-Api-Result'] = parsed_api_result
        # print(f"{headers=}")
        # flask_resp = flask.Response(resp.content, status=resp.status_code, headers=headers)
        # return flask_resp, [parsed_api_result.get('id')]
        return forward_and_process_response()
    except Exception as e:
        print(e)
        return jsonify({'error': e}), 500


@resource_bp.route('/files/create_folder_v2', methods=['GET', 'POST'])
@require_oauth_stateful()
@update_history_proxy(session=db.session)
def create_folder():
    """Create a folder under the /Apps/Joplin folder."""
    try:
        return forward_and_process_response()
    except Exception as e:
        print(e)
        return jsonify({'error': e}), 500


@resource_bp.route('/files/upload', methods=['POST'])
@require_oauth_stateful()
@update_history_proxy(session=db.session)
def upload_file():
    """Upload a file to the /Apps/Joplin folder."""
    try:
        return forward_and_process_response()
    except Exception as e:
        print(e)
        return jsonify({'error': e}), 500
    

@resource_bp.route('/files/delete_v2', methods=['POST'])
@require_oauth_stateful()
@update_history_proxy(session=db.session)
def delete_file():
    """Delete a file in the /Apps/Joplin folder."""
    try:
        return forward_and_process_response()
    except Exception as e:
        print(e)
        return jsonify({'error': e}), 500


@resource_bp.route('/files/delete_batch', methods=['POST'])
@require_oauth_stateful()
@update_history_proxy(session=db.session)
def delete_batch():
    """Delete a bathc of files in the /Apps/Joplin folder."""
    try:
        return forward_and_process_response()
    except Exception as e:
        print(e)
        return jsonify({'error': e}), 500


@resource_bp.route('/files/delete_batch/check', methods=['POST'])
@require_oauth_stateful()
@update_history_proxy(session=db.session)
def delete_batch_check():
    """Delete a bathc of files in the /Apps/Joplin folder."""
    try:
        return forward_and_process_response()
    except Exception as e:
        print(e)
        return jsonify({'error': e}), 500


def forward_and_process_response():
    """Forward the request to the real Dropbox server."""
    request = flask.request
    print(f"{request.url=}, {request.path=}")
    print(f"{request.headers=}")
    url_path = request.path[4:]
    base_url = DROPBOX_CONTENT_BASE_URL if url_path in ['/files/upload', '/files/download'] else DROPBOX_API_BASE_URL
    url = f"{base_url}{url_path}"
    urlparse_result = urlparse(url)
    host = urlparse_result.netloc
    print(f"{url=}")
    # Update the access token and host in the request headers.
    req_headers = dict(request.headers)
    req_headers.update({'Authorization': f"Bearer {flask.current_app.config['DROPBOX_OAUTH2_ACCESS_TOKEN']}",
                        'Host': host})
    if 'Dropbox-Api-Arg' in request.headers:
        # If the args are request.headers['Dropbox-API-Arg'], update the relative path to the absolute path.
        parsed_api_args = json.loads(req_headers.get('Dropbox-Api-Arg'))
        path = parsed_api_args['path']
        abspath = f"/Apps/JoplinDev{path}"
        parsed_api_args.update({'path': abspath})
        # Replace the proxy access token with the real access token from Dropbox, and the arguments with the updated path.
        req_headers.update({'Dropbox-Api-Arg': json.dumps(parsed_api_args)})
        resp = requests.request(
            method=request.method,
            url=url,    # Replace the URL with the real Dropbox API URL.
            headers=req_headers,
            data=request.get_data(),
            cookies=request.cookies)
    # If the args are in request body, update the relative path to the absolute path.
    else:
        body = request.get_json()
        if 'path' in body:
            path = body.get('path')
            abspath = f"/Apps/JoplinDev{path}"
            body.update({'path': abspath})
        elif 'entries' in body:
            for entry in body.get('entries'):
                path = entry.get('path')
                abspath = f"/Apps/JoplinDev{path}"
                entry.update({'path': abspath})
        resp = requests.request(
            method=request.method,
            url=url,    # Replace the URL with the real Dropbox API URL.
            headers=req_headers,
            json=body,
            cookies=request.cookies)
    print(f"{resp.headers=}")
    print(f"{resp.content=}")
    resp_headers = dict(resp.headers)
    # HACK: Remove 'Content-Encoding' to avoid error.
    if 'Content-Encoding' in resp_headers and resp_headers['Content-Encoding'] == 'gzip':
        del resp_headers['Content-Encoding']
    print(f"{resp.headers=}")
    # Get object ids from the response.
    ids = []
    if resp.status_code == 200:
        if resp.headers['Content-Type'] == 'application/json':
            resp_json = json.loads(resp.content)
            if 'path_lower' in resp_json:
                ids = [resp_json.get('path_lower')]
            if 'entries' in resp_json:
                entries = resp_json.get('entries')
                ids = [e.get('path_lower') for e in entries]
            if 'metadata' in resp_json:
                md = resp_json.get('metadata')
                ids = [md.get('path_lower')]
        if 'Dropbox-Api-Result' in resp.headers:
            resp_headers = dict(resp.headers)
            parsed_api_result = json.loads(resp_headers.get('Dropbox-Api-Result'))
            resp_headers['Dropbox-Api-Result'] = parsed_api_result
            ids = [parsed_api_result.get('path_lower')]
    # Construct the flask response to send back to the client.
    flask_resp = flask.Response(resp.content, status=resp.status_code, headers=resp_headers)
    return flask_resp, ids

def init_server_api(app):
    """Initialize the proxy as a client of the real server."""
    # Start OAuth2 flow
    auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY,
                                consumer_secret=APP_SECRET,
                                token_access_type="offline",
                                # scope=SCOPES
                                )

    authorize_url = auth_flow.start()
    print("1. Go to the following url to authorize this application:")
    print(authorize_url)
    auth_code = input("2. Enter the authorization code here: ").strip()


    try:
        oauth_result = auth_flow.finish(auth_code)
        # assert oauth_result.scope == SCOPES
    except Exception as e:
        print('Error: %s' % (e,))
        sys.exit(1)

    with dropbox.Dropbox(oauth_result.access_token) as dbx:
        try:
            dbx.users_get_current_account()
        except AuthError as e:
            print('AuthError: %s' % (e,))
            sys.exit(1)

    app.config.update({
        'DROPBOX_OAUTH2_ACCESS_TOKEN': oauth_result.access_token,
        'DROPBOX_OAUTH2_USER_ID': oauth_result.account_id,
    })


def register_resource_blueprint(app):
    """ Register the resource server endpoints."""
    init_server_api(app)
    app.register_blueprint(resource_bp, url_prefix='/api')
