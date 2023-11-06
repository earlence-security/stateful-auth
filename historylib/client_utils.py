from .history import History
from .history_list import HistoryList
from .batch_history_list import BatchHistoryList
import os
import json

# Our Client stores history in files with obj_id as filename,
# content is json of form: 
# {
#   Token1 = [history1, history2, …..]
#   Token2 = [history1, history2, …..]
#   ………
# }

def load_history_file_to_dict(filename, path):
    file_path = os.path.join(path, filename)
    with open(file_path) as json_file:
        history_dict = json.load(json_file)
        return history_dict
    

def history_to_file(history_list: HistoryList, filename, path, token):
    if filename == "":
        return
    file_path = os.path.join(path, filename)
    history_storage_json = ""
    if (os.path.exists(file_path)):
        history_dict = load_history_file_to_dict(filename, path)
        history_dict[token] = history_list.to_dict()[history_list.obj_id]
        history_storage_json = json.dumps(history_dict)
    else:
        history_dict = history_list.to_dict()
        history_storage_dict = {token: history_dict[history_list.obj_id]}
        history_storage_json = json.dumps(history_storage_dict)
    
    with open(file_path, "w") as outfile:
        outfile.write(history_storage_json)


def batch_history_to_file(history_lists: BatchHistoryList, path, token):
    for obj_id, history_list in history_lists.entries.items():
        history_to_file(history_list, obj_id, path, token)


# get historyList from directory storing history json files for this token, if not found return empty historylist
def get_history(obj_id, directory, token):
    file_path = os.path.join(directory, obj_id)

    if not os.path.isfile(file_path):
        return HistoryList()
    
    hist_dict = load_history_file_to_dict(obj_id, directory)
    if token in hist_dict:
        history_list_dict = hist_dict[token]
        history_list = HistoryList(obj_id=obj_id, json_str=json.dumps(history_list_dict))
        return history_list
    else:
        return HistoryList()
    
# get batch of historyList from directory storing history json files for this token, if not found return empty historylist
def get_batchhistory(filename_list: list, directory, token):
    history_lists = []
    for filename in filename_list:
        history_lists.append(get_history(filename, directory, token))
    return BatchHistoryList(historylists=history_lists)


def delete_history_file(filename, directory):
    file_path = os.path.join(directory, filename)
    os.remove(file_path)
