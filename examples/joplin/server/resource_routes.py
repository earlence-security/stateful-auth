import sys
import flask
import dropbox

from flask import Blueprint, jsonify, make_response
from dropbox import DropboxOAuth2FlowNoRedirect
from dropbox.exceptions import AuthError
from authlib.integrations.flask_oauth2 import current_token

from proxy.oauth2 import require_oauth_stateful
from proxy.models import db
from historylib.proxy_utils import update_history_proxy

# OAuth2 configurations
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


@resource_bp.route('/list-folder')
@require_oauth_stateful()
@update_history_proxy(session=db.session)
def list_folder():
    """List the content of the /Apps/Joplin folder."""
    with dropbox.Dropbox(flask.current_app.config['DROPBOX_OAUTH2_ACCESS_TOKEN']) as dbx:
        try:
            result = dbx.files_list_folder(path='')
            resp = make_response(jsonify([(e.id, e.name) for e in result.entries]))
            return resp, [e.id for e in result.entries]
        except dropbox.exceptions.ApiError as e:
            print(e)
            return jsonify({'error': 'An error occured'}), 500


def init_server_api(app):
    """ Initialize the proxy as a client of the real server."""
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
