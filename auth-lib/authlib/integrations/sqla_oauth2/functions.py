import time
from authlib.oauth2.rfc6750.errors import (
    PolicyFailedError, BadPolicyEndpointError, PolicyHashMismatchError, PolicyCrashedError, InvalidHistoryError
)

import time

from flask import jsonify, g, current_app

from authlib.oauth2.stateful.validator_helper import (
    run_policy, build_request_JSON
)
from wasmtime import Config, Engine, Linker, Module
from historylib.batch_history_list import BatchHistoryList
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

def create_bearer_token_validator_stateful(wasm_linker, session, token_model, client_model, policy_model, is_proxy=False):

    from authlib.oauth2.stateful import BearerTokenValidatorStateful

    class _BearerTokenValidatorStateful(BearerTokenValidatorStateful):

        def authenticate_token(self, token_string):
            q = session.query(token_model)
            return q.filter_by(access_token=token_string).first()
        
        # extra stateful checks 
        def validate_token_stateful(self, token, scopes, request,):

            q = session.query(client_model)
            client = q.filter_by(client_id=token.client_id).first()

            # LOGGING
            if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
                and hasattr(g, 'current_log'):
                history_validation_start = time.time()

            if is_proxy:
                from historylib.proxy_utils import validate_object_ids_proxy
                #if not validate_object_ids_proxy(session):
                    #print("!!!!!!!!!!!!!!! invalid object_id !!!!!!!!!!!!!!!!!!")
                    # raise InvalidHistoryError()
            else:
                # Check for history integrity
                if not validate_history(session):
                    print("!!!!!!!!!!!!!!! invalid history !!!!!!!!!!!!!!!!!!")
                    raise InvalidHistoryError()

            # LOGGING
            if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
                and hasattr(g, 'current_log'):
                history_validation_time = time.time() - history_validation_start

            # get module from some db
            policy_q = session.query(policy_model)
            policy = policy_q.filter_by(policy_hash=token.policy).first()
            policy_module = Module.deserialize(wasm_linker.engine, policy.serialized_module)

            request_JSON, request_size = build_request_JSON(request)
            if is_proxy:
                # Get history list from server-side DB (only for proxy)
                from historylib.proxy_utils import get_history_list_str_proxy
                history_list_str = get_history_list_str_proxy(session)
            else:
                # Get history list from request header
                history_list_str = request.headers.get('Authorization-History')
                # history_list = BatchHistoryList() if not history_list_str else BatchHistoryList(json_str=history_list_str)

            # print(f"{request_JSON=}")
            # LOGGING
            if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
                and hasattr(g, 'current_log'):
                policy_execution_start = time.time()
            try:
                # run the policy, accept/deny based on output
                # result = run_policy(wasm_linker, policy_module, policy.policy_hash, request_JSON, history_list.to_json())
                # print("request input to policy program is: ", request_JSON)
                # print("history input to policy program is: ", history_list_str)
                result = run_policy(wasm_linker, policy_module, policy.policy_hash, request_JSON, history_list_str)
            except Exception as e:
                print(e)
                raise PolicyCrashedError()
            
            # LOGGING
            if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
                and hasattr(g, 'current_log'):
                policy_execution_time = time.time() - policy_execution_start

            # LOGGING
            if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
                and hasattr(g, 'current_log'):
                history_size = len(history_list_str)
                batch_history_list = BatchHistoryList(json_str=history_list_str)
                history_length = batch_history_list.get_num_history_entries()
                # Save to the current log in LogManager
                current_log = g.current_log
                current_log.history_validation_time = history_validation_time
                current_log.policy_execution_time = policy_execution_time
                current_log.request_size = request_size
                if 'Content-Length' in request.headers:
                    request_data_size = int(request.headers['Content-Length'])
                    current_log.request_data_size = request_data_size
                current_log.history_size = history_size
                current_log.history_length = history_length

            if not result:
                raise PolicyFailedError()

    return _BearerTokenValidatorStateful
