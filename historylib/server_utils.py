import functools
import flask
from flask import Request, Response

from .history import History
from .history_list import HistoryList
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
    """Returns whether a history list in the request header is valid."""
    request = flask.request
    # NOTE: We assume here that the object id is the first argument in the url.
    if list(request.view_args.values()):
        object_id = list(request.view_args.values())[0]
        token = get_token_from_request(request)
        history_list_hash_row = session.query(HistoryListHash).filter_by(object_id=object_id, access_token=token).first()
        history_list = HistoryList(request.headers.get('Authorization-History'))
        if not history_list_hash_row:
            if not history_list.entries:
                return True
            else:
                return False
        return history_list_hash_row.history_list_hash == history_list.to_hash()
    else:
        return request.headers.get('Authorization-History') == ''

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
            if (request.method == 'POST' or request.method == 'GET') and len(ids) == 1:
                # Create new history entry and append to history list
                object_id = ids[0]
                new_history = History(request.path, request.method)
                history_list_hash_row = session.query(HistoryListHash).filter_by(object_id=object_id, access_token=token).first()

                if history_list_hash_row:
                    # Existing object, update history list hash
                    history_list = HistoryList(request.headers.get('Authorization-History'))
                    history_list.append(new_history)
                    history_list_hash_row.history_list_hash = history_list.to_hash()
                    session.commit()
                else:
                    # New object, create history list hash
                    history_list = HistoryList()
                    history_list.append(new_history)
                    history_list_hash = HistoryListHash(
                        object_id=object_id,
                        access_token=token,
                        history_list_hash=history_list.to_hash()
                    )
                    session.add(history_list_hash)
                    session.commit()

                # Add updated history list to the response header
                resp.headers['Set-Authorization-History'] = history_list.to_json()
                return resp
            elif request.method == 'DELETE' and len(ids) == 1:
                object_id = ids[0]
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

