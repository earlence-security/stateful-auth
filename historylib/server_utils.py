"""Historylib utils for server. Server stores the hash values of objects histories."""
import functools
import flask
import uuid
import time
from flask import Request, Response, g, current_app
from urllib.parse import urlparse
import json
import hashlib

from .history import History
from .history_list import HistoryList
from .batch_history_list import BatchHistoryList
from server.website.models import HistoryListHash, OAuth2Client, UpdateProgram, OAuth2Token
from wasmtime import Module, Store, WasiConfig
import os
import tempfile

# In our server database, each object have a history field.
# history is a json string with form:
# {
#   token: hash(HistoryList)
#   token2: hash(HistoryList2)
#   ..........
# }
# Generate the json to be stored from historylist,
# if old_storage is provided, then update from that storage

def validate_history(session):
    """Returns whether a batch of history list in the request header is valid."""
    request = flask.request
    data = request.get_json(silent=True)
    token = get_token_from_request(request)

    # NOTE: We assume here that the object id is the first argument in the url.
    if list(request.view_args.values()):
        batch_history_list = BatchHistoryList(json_str=request.headers.get('Authorization-History'))
        object_id = list(request.view_args.values())[0]
        return validate_historylist(batch_history_list.entries.get(str(object_id), HistoryList(object_id)), object_id, token, request, session)
    # NOTE: We assume here batch object id is the ids field of body.
    elif data != None and 'ids' in data:
        batch_history_list = BatchHistoryList(json_str=request.headers.get('Authorization-History'))
        for object_id in data['ids']:
            object_id = uuid.UUID(object_id)
            if not validate_historylist(batch_history_list.entries.get(str(object_id), HistoryList(object_id)), object_id, token, request, session):
                return False
        return True
    else:
        return request.headers.get('Authorization-History') == ''
    

def validate_historylist(history_list, object_id, token, request, session):
    """Returns whether a history list in the request header is valid."""
    history_list_hash_row = session.query(HistoryListHash).filter_by(object_id=object_id, access_token=token).first()
    if not history_list_hash_row:
        if not history_list.entries:
            return True
        else:
            return False
    return history_list_hash_row.history_list_hash == history_list.to_hash()


def insert_historylist(request, object_id, session):
    """Update one single historylist in db."""
    token = get_token_from_request(request)
    new_history = History(request.path, request.method)
    history_list_hash_row = session.query(HistoryListHash).filter_by(object_id=object_id, access_token=token).first()

    history_list = HistoryList(obj_id=object_id)
    if history_list_hash_row:
        # Existing object, update history list hash
        old_batch_history_list = BatchHistoryList(json_str=request.headers.get('Authorization-History'))
        history_list = old_batch_history_list.entries[str(object_id)]
        history_list.append(new_history)
        history_list_hash_row.history_list_hash = history_list.to_hash()
        session.commit()
    else:
        # New object, create history list hash
        history_list.append(new_history)
        history_list_hash = HistoryListHash(
            object_id=object_id,
            access_token=token,
            history_list_hash=history_list.to_hash()
        )
        session.add(history_list_hash)
        session.commit()
    return history_list


def insert_historylist_wasm(linker, request, object_id, session):
    """Update one single historylist in db."""
    token = get_token_from_request(request)
    oauth2_token = session.query(OAuth2Token).filter_by(access_token=token).first()
    oauth2_client = session.query(OAuth2Client).filter_by(user_id=oauth2_token.user_id).first()
    update_program = session.query(UpdateProgram).filter_by(client_id=oauth2_client.client_id).first()

    history_list_hash_row = session.query(HistoryListHash).filter_by(object_id=object_id, access_token=token).first()

    history_list = HistoryList(obj_id=object_id)
    if history_list_hash_row:
        # Existing object, update history list hash
        old_batch_history_list = BatchHistoryList(json_str=request.headers.get('Authorization-History'))
        history_list = old_batch_history_list.entries[str(object_id)]
        
        newhist_string = run_update_program(linker, update_program, build_request_JSON(request), history_list.to_json())
        newhist_list = HistoryList(json_str=newhist_string)

        history_list_hash_row.history_list_hash = newhist_list.to_hash()
        session.commit()
        return newhist_list
    else:
        # New object, create history list hash

        #replace with wasm
        #history_list.append(new_history)
        newhist_string = run_update_program(linker, update_program, build_request_JSON(request), history_list.to_json())
        newhist_list = HistoryList(json_str=newhist_string)

        history_list_hash = HistoryListHash(
            object_id=object_id,
            access_token=token,
            history_list_hash=newhist_list.to_hash(),
        )
        session.add(history_list_hash)
        session.commit()
        return newhist_list


def run_update_program(wasm_linker, update_program, request_str, history_str):

    # newhistory = runwasm(old_history)
    # return newhistory

    config = WasiConfig()
    config.argv = (update_program.file_name, request_str, history_str)
    config.preopen_dir(".", "/")
    with tempfile.TemporaryDirectory() as chroot:

        out_log = os.path.join(chroot, "out.log")
        err_log = os.path.join(chroot, "err.log")
        config.stdout_file = out_log
        config.stderr_file = err_log

        # # LOGGING
        # policy_execution_start = time.time()

        # Store is a unit of isolation in wasmtime
        # containes wasm objects
        # We must have one Store per request, because Store dont' have GC and isolation.
        store = Store(wasm_linker.engine)
        store.set_wasi(config)

        # instantiated module
        # both new store and instantiate are very cheap
        deserialized_module = Module.deserialize(wasm_linker.engine, update_program.serialized_module)
        instance = wasm_linker.instantiate(store, deserialized_module)

        # _start is the default wasi main function
        start = instance.exports(store)["_start"]

        try:
            start(store)
        except Exception as e:
            print("error:", e)
            raise

        # # LOGGING
        # policy_execution_time = time.time() - policy_execution_start

        with open(out_log) as f:
            result = f.read()
            return result


def update_history(session, wasm_linker):
    def wrapper(f):
        """Decorator for updating history list hash in the database and stored in user-side."""
        @functools.wraps(f)
        def decorated(*args, **kwargs) -> Response:
            
            # Policy check and resource API call will happen in the function `f`.
            ret = f(*args, **kwargs)
            if not isinstance(ret, tuple) or ret[0].status_code >= 400 :
                # Resource API call failed, do nothing.
                return ret
            # Resource APIs return a tuple of (response, object_ids).
            resp = ret[0]
            ids = ret[1] if isinstance(ret[1], list) else [ret[1]]
            request = flask.request
            token = get_token_from_request(request)

            # LOGGING
            if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
                and hasattr(g, 'current_log'):
                history_update_start = time.time()

            # If create, update, or get an object, we should update the history list hash.
            if (request.method == 'POST' or request.method == 'GET'):
                newhistories = []
                for object_id in ids:
                    newhistory_list = insert_historylist_wasm(wasm_linker, request, object_id, session)
                    newhistories.append(newhistory_list)
                newhistories = BatchHistoryList(historylists=newhistories)

                # Add updated history list to the response header
                resp.headers['Set-Authorization-History'] = newhistories.to_json()
            elif request.method == 'DELETE':
                for object_id in ids:
                    history_list_hash = session.query(HistoryListHash).filter_by(object_id=object_id, access_token=token).first()
                    if history_list_hash:
                        session.delete(history_list_hash)
                        session.commit()

                resp.headers['Set-Authorization-History'] = ''
            else:
                # TODO: Add support for other methods, like `list`
                resp.headers['Set-Authorization-History'] = ''
            

            # LOGGING
            if 'ENABLE_LOGGING' in current_app.config and current_app.config['ENABLE_LOGGING'] \
                and hasattr(g, 'current_log'):
                current_log = g.current_log
                history_update_time = time.time() - history_update_start
                current_log.history_update_time = history_update_time
            
            return resp
            # TODO
            # for now assume single token operations
            # if old_storage != None:
            #     old_storage_dict = json.loads(old_storage)
        return decorated
    return wrapper


def get_token_from_request(request: Request):
    headers = request.headers
    bearer = headers.get('Authorization')
    token = bearer.split()[1]
    return token


def build_request_JSON(request):
    # Build JSON data for request
    request_data = {}
    request_data['method'] = request.method
    request_data['uri'] = request.url
    request_data['path'] = urlparse(request.url).path
    
    # check if request contain JSON body
    request_body = None
    headers = {k:v for k, v in request.headers.items()}
    if "Content-Type" in headers:
        if headers["Content-Type"] == "application/json":
            request_body = request.json
    
    if request_body == None:
        request_data['body'] = "null"
    else:
        request_data['body'] = json.dumps(request_body)

    request_data['headers'] = headers
    request_data['time'] = time.time()

    json_data = json.dumps(request_data)

    return json_data