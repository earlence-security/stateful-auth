"""Historylib utils for proxy. Proxy stores the entire history of objects instead of their hash values."""
import functools
import flask
import json

from flask import Request, Response, current_app

from historylib.history import History
from historylib.history_list import HistoryList
from historylib.batch_history_list import BatchHistoryList
from proxy.models import HistoryListRow


def validate_object_ids_proxy(session):
    """Returns whether object ids in the request header is valid.
    Every object id passed in the request must have a history list in the database.
    This function is only used for the proxy server."""
    # No need to validate object ids for proxy server.
    return True


def get_history_list_str_proxy(session):
    """Get historylist of all the objects in the current request from db.
    This function is only used for the proxy server."""
    request = flask.request
    token = get_token_from_request(request)
    # HACK: Dropbox API uses path instead of object id.
    if current_app.config['REAL_SERVER'] == 'Dropbox':
        object_ids = get_paths_from_request('/Apps/JoplinDev', request)
    else:
        object_ids = get_object_ids_from_request(request)

    history_list_batch = []
    for id in object_ids:
        history_list_row = session.query(HistoryListRow).filter_by(object_id=id, access_token=token).first()
        if not history_list_row:
            history_list_batch.append(HistoryList(obj_id=id))
        else:
            history_list_batch.append(HistoryList(json_str=history_list_row.history_list))

    return BatchHistoryList(historylists=history_list_batch).to_json()


def update_history_list_proxy(request, object_id, session):
    """Update one single historylist in db.
    This function is only used for the proxy server."""
    token = get_token_from_request(request)
    new_history = History(request.path, request.method)
    history_list_row = session.query(HistoryListRow).filter_by(object_id=object_id, access_token=token).first()

    if history_list_row:
        # Existing object, update history list
        # old_batch_history_list = BatchHistoryList(json_str=request.headers.get('Authorization-History'))
        # history_list = old_batch_history_list.entries[str(object_id)]
        history_list = HistoryList(json_str=history_list_row.history_list)
        history_list.append(new_history)
        history_list_row.history_list = history_list.to_json()
        session.commit()
    else:
        # New object, create history list
        history_list = HistoryList(obj_id=object_id)
        history_list.append(new_history)
        history_list_row = HistoryListRow(
            object_id=object_id,
            access_token=token,
            history_list=history_list.to_json()
        )
        session.add(history_list_row)
        session.commit()
    return history_list


def update_history_proxy(session):
    """Updating the history list in the server-side database.
    This function is only used for the proxy server."""
    def wrapper(f):
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
            if request.method == 'DELETE' or 'delete' in request.path.lower():
                for object_id in ids:
                    history_list_row = session.query(HistoryListRow).filter_by(object_id=object_id, access_token=token).first()
                    if history_list_row:
                        session.delete(history_list_row)
                        session.commit()
                return resp
            else:
                # Update the database row for each object accessed one by one.
                for object_id in ids:
                    update_history_list_proxy(request, object_id, session)
                return resp
        return decorated
    return wrapper


def get_object_ids_from_request(request: Request):
    """Get the object id from the request. This includes three cases:
        1. The object id is the first argument in the url.
        2. The object id is the ids field of body.
        3. The object id is not provided. This only happens when creating a new object.
    """
    request_json = request.get_json(silent=True)
    if list(request.view_args.values()):
        object_ids = [ list(request.view_args.values())[0] ]
    elif request_json != None and 'ids' in request_json:
        object_ids = request_json['ids']
    else:
        object_ids = []
    return object_ids


def get_paths_from_request(appdir: str, request: Request):
    """Return the paths in the request.
    This is only for the proxy server when the real server is Dropbox."""
    # HACK: We assume the object id will be passed by the request. But it is not always the case.
    # For example, Dropbox API accepts the path of the object instead of its id. We will reframe
    # this function so that the field name itself could be passed as an argument.
    body = request.get_json(silent=True)
    headers = request.headers
    paths = []
    if body:
        if 'path' in body:
            paths = [ f"{appdir}{body['path']}" ]
        elif 'entries' in body:
            paths = [ f"{appdir}{entry['path']}" for entry in body['entries'] ]
    elif 'Dropbox-Api-Arg' in headers:
        parsed_api_args = json.loads(headers.get('Dropbox-Api-Arg'))
        paths = [ f"{appdir}{parsed_api_args['path']}" ]
    paths = [p.lower() for p in paths]
    return paths


def get_token_from_request(request: Request):
    headers = request.headers
    bearer = headers.get('Authorization')
    token = bearer.split()[1]
    return token
