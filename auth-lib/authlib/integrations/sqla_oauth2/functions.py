import time
from authlib.oauth2.rfc6750.errors import (
    PolicyFailedError, BadPolicyEndpointError, PolicyHashMismatchError, PolicyCrashedError, InvalidHistoryError
)
import os
import requests
import hashlib
import json
import time
import tempfile

from flask import jsonify
from wasmtime import Config, Engine, Linker

from authlib.oauth2 import OAuth2Error
from authlib.oauth2.stateful.validator_helper import (
    run_policy, build_request_JSON
)
import tempfile
from wasmtime import Config, Engine, Linker, Module
from historylib.history import History
from historylib.history_list import HistoryList
from historylib.server_utils import validate_history

def create_query_client_func(session, client_model):
    """Create an ``query_client`` function that can be used in authorization
    server.

    :param session: SQLAlchemy session
    :param client_model: Client model class
    """
    def query_client(client_id):
        q = session.query(client_model)
        return q.filter_by(client_id=client_id).first()
    return query_client


def create_save_token_func(session, token_model):
    """Create an ``save_token`` function that can be used in authorization
    server.

    :param session: SQLAlchemy session
    :param token_model: Token model class
    """
    def save_token(token, request):
        if request.user:
            user_id = request.user.get_user_id()
        else:
            user_id = None
        client = request.client
        item = token_model(
            client_id=client.client_id,
            user_id=user_id,
            **token
        )
        session.add(item)
        session.commit()
    return save_token


def create_query_token_func(session, token_model):
    """Create an ``query_token`` function for revocation, introspection
    token endpoints.

    :param session: SQLAlchemy session
    :param token_model: Token model class
    """
    def query_token(token, token_type_hint):
        q = session.query(token_model)
        if token_type_hint == 'access_token':
            return q.filter_by(access_token=token).first()
        elif token_type_hint == 'refresh_token':
            return q.filter_by(refresh_token=token).first()
        # without token_type_hint
        item = q.filter_by(access_token=token).first()
        if item:
            return item
        return q.filter_by(refresh_token=token).first()
    return query_token


def create_revocation_endpoint(session, token_model):
    """Create a revocation endpoint class with SQLAlchemy session
    and token model.

    :param session: SQLAlchemy session
    :param token_model: Token model class
    """
    from authlib.oauth2.rfc7009 import RevocationEndpoint
    query_token = create_query_token_func(session, token_model)

    class _RevocationEndpoint(RevocationEndpoint):
        def query_token(self, token, token_type_hint):
            return query_token(token, token_type_hint)

        def revoke_token(self, token, request):
            now = int(time.time())
            hint = request.form.get('token_type_hint')
            token.access_token_revoked_at = now
            if hint != 'access_token':
                token.refresh_token_revoked_at = now
            session.add(token)
            session.commit()

    return _RevocationEndpoint


def create_bearer_token_validator(session, token_model):
    """Create an bearer token validator class with SQLAlchemy session
    and token model.

    :param session: SQLAlchemy session
    :param token_model: Token model class
    """
    from authlib.oauth2.rfc6750 import BearerTokenValidator

    class _BearerTokenValidator(BearerTokenValidator):
        def authenticate_token(self, token_string):
            q = session.query(token_model)
            return q.filter_by(access_token=token_string).first()

    return _BearerTokenValidator

def create_bearer_token_validator_stateful(wasm_linker, session, token_model, client_model, policy_model):

    from authlib.oauth2.stateful import BearerTokenValidatorStateful

    class _BearerTokenValidatorStateful(BearerTokenValidatorStateful):

        def authenticate_token(self, token_string):
            q = session.query(token_model)
            return q.filter_by(access_token=token_string).first()
        
        # extra stateful checks 
        def validate_token_stateful(self, token, scopes, request):

            q = session.query(client_model)
            client = q.filter_by(client_id=token.client_id).first()

            # Check for history integrity
            if not validate_history(session):
                raise InvalidHistoryError()

            policy_url = os.path.join(client.policy_endpoint, token.policy + ".wasm")
            # Put policy program in tmp for now
            with tempfile.TemporaryDirectory() as chroot:
                # Download the program from program endpoint
                # TODO: Don't use this method, put program directly in request
                program_name = policy_url.split("/")[-1]
                policy_file = os.path.join(chroot, policy_url.split("/")[-1])
                response = requests.get(policy_url)
                if response.status_code == 200:
                    policy_data = response.content
                    with open(policy_file, "wb") as file:
                        file.write(policy_data)
                else:
                    raise BadPolicyEndpointError()

            # get module from some db
            policy_q = session.query(policy_model)
            policy = policy_q.filter_by(policy_hash=token.policy).first()
            policy_module = Module.deserialize(wasm_linker.engine, policy.serialized_module)

            request_JSON = build_request_JSON(request)
            history_list_str = request.headers.get('Authorization-History')
            history_list = HistoryList() if not history_list_str else HistoryList(history_list_str)
            # TODO: Build JSON data for history
            try:
                # run the policy, accept/deny based on output
                result = run_policy(wasm_linker, policy_module, policy.policy_hash, request_JSON, history_list.to_json())
            except Exception as e:
                print(e)
                raise PolicyCrashedError()

            if not result:
                raise PolicyFailedError()
                

    return _BearerTokenValidatorStateful
