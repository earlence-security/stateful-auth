from .history import History
from .history_list import HistoryList
import json
from flask import Request

# In our server database, each object have a history field.
# history is a json string with form:
# {
#   token: hash(HistoryList)
#   token2: hash(HistoryList2)
#   ..........
# }
# Generate the json to be stored from historylist,
# if old_storage is provided, then update from that storage
def historylist_to_storage_json(history_list: HistoryList, request: Request, old_storage=None):
    token = get_token_from_request(request)
    history_storage_dict = {token: history_list.to_hash()}

    # TODO
    # for now assume single token operations
    if old_storage != None:
        old_storage_dict = json.loads(old_storage)

    return json.dumps(history_storage_dict)


def get_token_from_request(request: Request):
    headers = request.headers
    bearer = headers.get('Authorization')
    token = bearer.split()[1]
    return token

