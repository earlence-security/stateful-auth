"""Historylib utils for server. Server stores the hash values of objects histories."""
import os
import tempfile
import functools
import flask
import time
import re
import ujson as json
import hashlib
import json
import multiprocessing
import concurrent.futures
import hmac

from uuid import UUID
from flask import Request, Response, g, current_app
from urllib.parse import urlparse
from wasmtime import Module, Store, WasiConfig
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from itertools import repeat


from .history import History
from .history_list import HistoryList
from .batch_history_list import BatchHistoryList
from server.website.models import HistoryListHash, OAuth2Client, UpdateProgram, OAuth2Token, db


# In our server database, each object have a history field.
# history is a json string with form:
# {
#   token: hash(HistoryList)
#   token2: hash(HistoryList2)
#   ..........
# }
# Generate the json to be stored from historylist,
# if old_storage is provided, then update from that storage

def find_key_value(json_string, target_key):
    pattern = r'"' + re.escape(target_key) + r'"\s*:\s*\[([^\]]*)\]'
    match = re.search(pattern, json_string)
    if match:
        return '[' + match.group(1).strip() + ']'
    else:
        return None

def validate_historylist_multiprocessing(history_list, object_id, token, db_url):
    """Returns whether a history list in the request header is valid."""
    db_engine = create_engine(db_url)
    Session = sessionmaker(bind=db_engine)
    session = Session()
    history_list_hash_row = session.query(HistoryListHash).filter_by(object_id=UUID(object_id), access_token=token).first()
    oauth2_token = session.query(OAuth2Token).filter_by(access_token=token).first()
    oauth2_client = session.query(OAuth2Client).filter_by(client_id=oauth2_token.client_id).first()
    session.close()

    hmac_key = oauth2_client.hmac_key
    if not history_list_hash_row:
        # TODO: Recover this.
        # if not history_list.entries:
        #     return True
        # else:
        #     return False
        return True
    return history_list_hash_row.history_list_hash == HistoryList(object_id=object_id, json_str=history_list).to_hmac(hmac_key)


def validate_historylist(history_list, object_id, token, session, app, hmac_key):
    """Returns whether a history list in the request header is valid."""
    # with app.app_context():
    history_list_hash_row = session.query(HistoryListHash).filter_by(object_id=UUID(object_id), access_token=token).first()
    value = history_list.to_hmac(hmac_key) if current_app.config['INTEGRITY_CHECK'] == 'hmac' else history_list.to_hash()
    if not history_list_hash_row:
        # TODO: Recover this.
        # if not history_list.entries:
        #     return True
        # else:
        #     return False
        return True
    return history_list_hash_row.history_list_hash == value


def validate_historylist_simple(history_list, row, hmac_key):
    """Returns whether a history list in the request header is valid."""
    # value = history_list.to_hash()
    value = history_list.to_hmac(hmac_key) if current_app.config['INTEGRITY_CHECK'] == 'hmac' else history_list.to_hash()
    if not row:
        # TODO: Recover this.
        # if not history_list.entries:
        #     return True
        # else:
        #     return False
        return True
    return row.history_list_hash == value


def validate_history(session):
    """Returns whether a batch of history list in the request header is valid."""
    request = flask.request
    # data = request.get_json(silent=True)
    data = request.get_json(silent=True)
    token = get_token_from_request(request)
    db_url = current_app.config['SQLALCHEMY_DATABASE_URI']

    # NOTE: We assume here that the object id is the first argument in the url.
    if list(request.view_args.values()):
        batch_history_list = BatchHistoryList(json_str=request.headers.get('Authorization-History'))
        object_id = list(request.view_args.values())[0]
        return validate_historylist(batch_history_list.entries.get(str(object_id), HistoryList(object_id)), object_id, token, session)
    # NOTE: We assume here batch object id is the ids field of body.
    elif data != None and 'ids' in data:
        hmac_key = None
        if current_app.config['INTEGRITY_CHECK'] == 'hmac':
            oauth2_token = session.query(OAuth2Token).filter_by(access_token=token).first()
            oauth2_client = session.query(OAuth2Client).filter_by(client_id=oauth2_token.client_id).first()        
            hmac_key = oauth2_client.hmac_key

        # Opt 1: Sequential
        batch_history_list = BatchHistoryList(json_str=request.headers.get('Authorization-History'))
        for object_id in data['ids']:
            if not validate_historylist(batch_history_list.entries.get(str(object_id), HistoryList(object_id)), object_id, token, session, current_app, hmac_key):
                return False
        return True
    
        # Opt 2: Fetch all the state hmacs for this token
        # batch_history_list = BatchHistoryList(json_str=request.headers.get('Authorization-History'))
        # hamcs = session.query(HistoryListHash).filter_by(access_token=token).all()
        # hmacs = {h.object_id: h.history_list_hash for h in hamcs}
        # for object_id in data['ids']:
        #     if not validate_historylist_simple(batch_history_list.entries.get(str(object_id), HistoryList(object_id)), hmacs.get(object_id), hmac_key):
        #         return False
        # return True

        # Opt 3: Multiprocessing - 1
        # batch_history_list = json.loads(request.headers.get('Authorization-History'))
        # with multiprocessing.Pool(2) as p:
        #     results = p.starmap(validate_historylist_multiprocessing, [(batch_history_list[object_id], object_id, token, db_url) for object_id in data['ids']])
        # return all(results)

        # Opt 4: Multiprocessing - 2
        # batch_history_list = json.loads(request.headers.get('Authorization-History'))
        # with ProcessPoolExecutor(max_workers=4) as executor:
        #     results = executor.map(validate_historylist_multiprocessing, batch_history_list.values(), data['ids'], repeat(token), repeat(db_url))
        # return all(results)
        
        # Opt 5: Multithreading
        # batch_history_list = json.loads(request.headers.get('Authorization-History'))
        # batch_history_list = BatchHistoryList(json_str=request.headers.get('Authorization-History'))
        # with ThreadPoolExecutor(max_workers=1) as executor:
        #     app = current_app._get_current_object()
        #     # futures = {executor.submit(validate_historylist, batch_history_list[object_id], object_id, token, session, app, hmac_key): object_id for object_id in data['ids']}
        #     futures = {executor.submit(validate_historylist, batch_history_list.entries.get(object_id), object_id, token, session, app, hmac_key): object_id for object_id in data['ids']}
        #     for future in concurrent.futures.as_completed(futures):
        #         object_id = futures[future]
        #         try:
        #             result = future.result()
        #         except Exception as e:
        #             print(e)
        #             return False
        #         if not result:
        #             return False
        #         # print(object_id, result)
        #     return True
    else:
        # HACK: for latency measurement, we assume the initial history list is valid.
        return True
        # return request.headers.get('Authorization-History') == ''


# deprecated and not used
def insert_historylist(request, object_id, session):
    """Update one single historylist in db."""
    token = get_token_from_request(request)
    new_history = History(request.path, request.method)
    # t = time.time()
    history_list_hash_row = session.query(HistoryListHash).filter_by(object_id=object_id, access_token=token).first()
    # t = time.time() - t
    # print("query_historylist", object_id, t)

    history_list = HistoryList(obj_id=object_id)
    if history_list_hash_row:
        # t = time.time()
        # Existing object, update history list hash
        old_batch_history_list = BatchHistoryList(json_str=request.headers.get('Authorization-History'))
        history_list = old_batch_history_list.entries[str(object_id)]
        # HACK: for measurement, it won't update the history list. So the history is always valid.
        # history_list.append(new_history)    # TODO: Recover this.
        history_list_hash_row.history_list_hash = history_list.to_hash()
        # t = time.time() - t
        # print("update_historylist", object_id, t)
    else:
        # New object, create history list hash
        # HACK: for latency measurement, we assume the initial history list comes from the client.
        # print("insert_historylist", object_id)
        # t = time.time()

        # Approach 1: use re
        # history_list = find_key_value(request.headers.get('Authorization-History'), str(object_id))

        # Approach 2: use orjson
        batch_history_list = json.loads(request.headers.get('Authorization-History'))
        history_list = {str(object_id): batch_history_list[str(object_id)]}
        # print(history_list)
        history_list_hash = hashlib.sha256(json.dumps(history_list).encode()).hexdigest()
        # print("parse_json", object_id, time.time() - t)
        # history_list.append(new_history)    # TODO: Recover this.
        history_list_hash = HistoryListHash(
            object_id=object_id,
            access_token=token,
            history_list_hash=history_list_hash
        )
        session.add(history_list_hash)
        # t = time.time() - t
        # print("insert_historylist", object_id, t)
    return {str(object_id): history_list}


def to_hmac(object_id, history_list_str, key):
    history_list = HistoryList(obj_id=object_id, json_str=history_list_str)
    result = hmac.new(key.encode(), history_list.to_json().encode(), hashlib.sha256).hexdigest()
    return result


def insert_batch_history_wasm(linker, request, ids, session):
    token = get_token_from_request(request)
    oauth2_token = session.query(OAuth2Token).filter_by(access_token=token).first()
    update_program = session.query(UpdateProgram).filter_by(client_id=oauth2_token.client_id).first()
    # NOTE: Fix in main branch of this location.
    hmac_key = None
    if current_app.config['INTEGRITY_CHECK'] == 'hmac':
        oauth2_client = session.query(OAuth2Client).filter_by(client_id=oauth2_token.client_id).first()
        hmac_key = oauth2_client.hmac_key

    history_list_str = request.headers.get('Authorization-History')
    # print("History in request:", history_list_str)
    # NOTE: We can require the client to always pass {object_id: ""} in the header when there is no history.
    # history_list = json.loads(history_list_str) if history_list_str else {}
    # for id in ids:
    #     if str(id) not in history_list:
    #         history_list.update({str(id): {}})
    # start = time.time()
    new_batch_history_list_str = run_update_program(linker, update_program, build_request_JSON(request), history_list_str)
    # print("Wasm execution time:", time.time() - start)
    # print("History in response:", new_history_list_str)
    # start = time.time()
    new_history_list = json.loads(new_batch_history_list_str)
    rows = []
    # with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    #     futures = {executor.submit(to_hmac, object_id, new_history_list_str, hmac_key): object_id for object_id, new_history_list_str in new_history_list.items()}
    #     for future in concurrent.futures.as_completed(futures):
    #         object_id = futures[future]
    #         try:
    #             result = future.result()
    #         except Exception as e:
    #             print(e)
    #             raise e
    #         rows.append(HistoryListHash(
    #             object_id=UUID(object_id),
    #             access_token=token,
    #             history_list_hash=result
    #         ))
    rows = [
        HistoryListHash(
            object_id=object_id,
            access_token=token,
            history_list_hash=(
                HistoryList(obj_id=object_id, json_str=new_history_list[str(object_id)]).to_hmac(hmac_key) \
                if current_app.config['INTEGRITY_CHECK'] == 'hmac' \
                else HistoryList(obj_id=object_id, json_str=new_history_list[str(object_id)]).to_hash()
            ),
        ) for object_id in ids
    ]
    session.bulk_save_objects(rows)
    session.commit()
    # print("DB commit time:", time.time() - start)
    return new_batch_history_list_str


def insert_historylist_wasm_old(linker, request, object_id, session):
    """Update one single historylist in db."""
    token = get_token_from_request(request)
    oauth2_token = session.query(OAuth2Token).filter_by(access_token=token).first()
    oauth2_client = session.query(OAuth2Client).filter_by(user_id=oauth2_token.user_id).first()
    update_program = session.query(UpdateProgram).filter_by(client_id=oauth2_client.client_id).first()
    hmac_key = oauth2_client.hmac_key

    history_list_hash_row = session.query(HistoryListHash).filter_by(object_id=object_id, access_token=token).first()

    history_list = HistoryList(obj_id=object_id)
    if history_list_hash_row:
        # Existing object, update history list hash
        old_batch_history_list = BatchHistoryList(json_str=request.headers.get('Authorization-History'))
        history_list = old_batch_history_list.entries[str(object_id)]
        
        newhist_string = run_update_program(linker, update_program, build_request_JSON(request), history_list.to_json())
        newhist_list = HistoryList(json_str=newhist_string)

        history_list_hash_row.history_list_hash = newhist_list.to_hmac(hmac_key)
        session.commit()
        return newhist_list
    else:
        # New object, create history list hash

        #replace with wasm
        #history_list.append(new_history)
        # newhist_string = run_update_program(linker, update_program, build_request_JSON(request), history_list.to_json())
        # newhist_list = HistoryList(json_str=newhist_string)
        batch_history_list = json.loads(request.headers.get('Authorization-History'))
        history_list = {str(object_id): batch_history_list[str(object_id)]}

        history_list_hash_row = HistoryListHash(
            object_id=object_id,
            access_token=token,
            history_list_hash=history_list.to_hmac(hmac_key),
        )
        session.add(history_list_hash_row)
        session.commit()
        return history_list



def insert_historylist_wasm(linker, request, object_id, session, batch_history_list_json):
    """Update one single historylist in db."""
    token = get_token_from_request(request)
    oauth2_token = session.query(OAuth2Token).filter_by(access_token=token).first()
    update_program = session.query(UpdateProgram).filter_by(client_id=oauth2_token.client_id).first()

    history_list_hash_row = session.query(HistoryListHash).filter_by(object_id=object_id, access_token=token).first()

    history_list_json = json.dumps({str(object_id): batch_history_list_json[str(object_id)]})
    # print("History in request:", history_list_json)
    newhist_string = run_update_program(linker, update_program, build_request_JSON(request), history_list_json)
    newhist_list = {str(object_id): newhist_string}
    if history_list_hash_row:
        # Existing object, update history list hash
        # old_batch_history_list = BatchHistoryList(json_str=request.headers.get('Authorization-History'))
        history_list_hash_row.history_list_hash = hashlib.sha256(json.dumps(newhist_list).encode()).hexdigest()
        session.commit()
    else:
        # New object, create history list hash
        history_list_hash = hashlib.sha256(json.dumps(newhist_list).encode()).hexdigest()
        history_list_hash_row = HistoryListHash(
            object_id=object_id,
            access_token=token,
            history_list_hash=history_list_hash,
        )
        session.add(history_list_hash_row)
        session.commit()
    return newhist_list


def run_update_program(wasm_linker, update_program, request_str, history_str):

    # newhistory = runwasm(old_history)
    # return newhistory
    # Handling empty history string
    if not history_str:
        history_str = '{}'
    config = WasiConfig()
    config.argv = (update_program.file_name, request_str, history_str)
    config.preopen_dir(".", "/")
    with tempfile.TemporaryDirectory() as chroot:

        out_log = os.path.join(chroot, "out_1.log")
        err_log = os.path.join(chroot, "err_1.log")
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
            # print("result:", result)
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
                # Opt 1: Update batch history by iterating them in Python.
                # batch_history_list_json = json.loads(request.headers.get('Authorization-History'))
                # newhistories = {}
                # for object_id in ids:
                #     newhistory_list = insert_historylist_wasm_old(wasm_linker, request, object_id, session) 
                #                                              batch_history_list_json=batch_history_list_json)
                #     newhistories.update(newhistory_list)
                # print("History in response:", newhistories)
                # resp.headers['Set-Authorization-History'] = json.dumps(newhistories)
                
                # Opt 2: Update batch history by iterating them in Wasm.
                new_history_list_str = insert_batch_history_wasm(wasm_linker, request, ids, session)
                resp.headers['Set-Authorization-History'] = new_history_list_str

                # Opt 3: Update batsh history with multi-processing in Python.

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
