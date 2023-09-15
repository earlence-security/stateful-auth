import time
import flask
from flask import Blueprint, request, session, url_for
from flask import render_template, redirect, jsonify
from werkzeug.security import gen_salt
from authlib.oauth2 import OAuth2Error
from authlib.oauth2.rfc6750 import UnregisteredPolicyError
from .models import db, User, OAuth2Client
from .oauth2 import authorization
from .utils import current_user, split_by_crlf


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/', methods=('GET', 'POST'))
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        session['id'] = user.id
        # if user is not just to log in, but need to head back to the auth page, then go for it
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect('/')
    user = current_user()
    if user:
        clients = OAuth2Client.query.filter_by(user_id=user.id).all()
    else:
        clients = []

    return render_template('home.html', user=user, clients=clients)


@auth_bp.route('/logout')
def logout():
    del session['id']
    return redirect('/')


@auth_bp.route('/create_client', methods=('GET', 'POST'))
def create_client():
    user = current_user()
    if not user:
        return redirect('/')
    if request.method == 'GET':
        return render_template('create_client.html')

    client_id = gen_salt(24)
    client_id_issued_at = int(time.time())
    client = OAuth2Client(
        client_id=client_id,
        client_id_issued_at=client_id_issued_at,
        user_id=user.id,
    )

    form = request.form
    # This `client_metadata` is stored as json in db.Client model.
    client_metadata = {
        "client_name": form["client_name"],
        "client_uri": form["client_uri"],
        "grant_types": split_by_crlf(form["grant_type"]),
        "redirect_uris": split_by_crlf(form["redirect_uri"]),
        "response_types": split_by_crlf(form["response_type"]),
        "scope": form["scope"],
        "token_endpoint_auth_method": form["token_endpoint_auth_method"],
        # Save stateless policy in DB
        "policy_hashes": split_by_crlf(form["policy_hashes"]),
        # the endpoint for getting policies
        "policy_endpoint": form["policy_endpoint"],
    }
    client.set_client_metadata(client_metadata)

    if form['token_endpoint_auth_method'] == 'none':
        client.client_secret = ''
    else:
        client.client_secret = gen_salt(48)

    db.session.add(client)
    db.session.commit()
    return redirect('/')

# TODO: Check if policy is recorded.
@auth_bp.route('/oauth/authorize', methods=['GET', 'POST'])
def authorize():
    user = current_user()
    # if user log status is not true (Auth server), then to log it in
    if not user:
        return redirect(url_for('home.home', next=request.url))
    if request.method == 'GET':
        # TODO: Check if policy is recorded.
        # -------------------------------------
        try:
            client_id = request.args.get("client_id")
            policy = request.args.get("policy_hash")
            # TODO
            # if policy is None:
                # raise NotStatefulException()
        # except NotStatefulException as e:
            # print("An error occurred:", e)
        except ValueError as error:
            return error.error, 400
        
        # TODO handle Null client
        client = OAuth2Client.query.filter_by(client_id=client_id).first()
        if policy not in client.client_metadata.get("policy_hashes"):
            return UnregisteredPolicyError().error, 403

        try:
            grant = authorization.get_consent_grant(end_user=user)
        except OAuth2Error as error:
            return error.error, 403
        return render_template('authorize.html', user=user, grant=grant, policy=policy)
    if not user and 'username' in request.form:
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
    if request.form['confirm']:
        grant_user = user
    else:
        grant_user = None
    return authorization.create_authorization_response(grant_user=grant_user)


@auth_bp.route('/oauth/token', methods=['POST'])
def issue_token():
    # NOTE: `token` is generated in AuthorizationCodeGrant.create_token_response.
    # See https://github.com/lepture/authlib/blob/master/authlib/oauth2/rfc6749/grants/authorization_code.py#L238C30-L238C30.
    # token generates in auth-lib\authlib\oauth2\rfc6749\grants\authorization_code.py
    return authorization.create_token_response()


@auth_bp.route('/oauth/revoke', methods=['POST'])
def revoke_token():
    return authorization.create_endpoint_response('revocation')
