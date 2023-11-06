import functools
import flask
import uuid
from flask import Request, Response

from .history import History
from .history_list import HistoryList
from .batch_history_list import BatchHistoryList
from Authorization_Server.website.models import HistoryListHash

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
    # print("history_list_hash_row.as_dict", history_list_hash_row.as_dict)
    # print("history_list", history_list)
    # print("history_list hash", history_list.to_hash())
    if not history_list_hash_row:
        if not history_list.entries:
            return True
        else:
            return False
    return history_list_hash_row.history_list_hash == history_list.to_hash()


# update one single historylist in db
def insert_historylist(request, object_id, session):
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


def update_history(session):
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
            # If create, update, or get an object, we should update the history list hash.
            if (request.method == 'POST' or request.method == 'GET'):
                history_lists = []
                for object_id in ids:
                    history_lists.append(insert_historylist(request, object_id, session))
                new_batch_history_list = BatchHistoryList(historylists=history_lists)
                # Add updated history list to the response header
                resp.headers['Set-Authorization-History'] = new_batch_history_list.to_json()
                return resp
            elif request.method == 'DELETE':
                for object_id in ids:
                    history_list_hash = session.query(HistoryListHash).filter_by(object_id=object_id, access_token=token).first()
                    if history_list_hash:
                        session.delete(history_list_hash)
                        session.commit()
                resp.headers['Set-Authorization-History'] = ''
                return resp
            else:
                # TODO: Add support for other methods, like `list`
                resp.headers['Set-Authorization-History'] = ''
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

