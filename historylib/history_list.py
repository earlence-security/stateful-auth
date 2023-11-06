# defines a list of history objects
# maxlen(list) = number of apis able to access this object

import time
import json
from .history import History
import hashlib

# {
#   obj_id1 : [history_entry1, history_entry2, ...]
# }
class HistoryList:
    # takes an obj_id and a json representation of a list of history objects
    def __init__(self, obj_id="", json_str=None):
        self.obj_id = str(obj_id)
        # list of History objects
        self.entries = []
        if json_str != None:
            history_dict_list = json.loads(json_str)
            for hist in history_dict_list:
                self.entries.append(History.from_dict(hist))


    def __str__(self):
        return "HistoryList: " + self.to_json()


    def append(self, history: History):
        # check for duplicate operation
        for index in range(len(self.entries)):
            if self.entries[index].api == history.api and self.entries[index].method == history.method:
                self.entries[index].counter += 1
                self.entries[index].timestamp = history.timestamp
                return

        self.entries.append(history)


    # this could be tricky because json to string don't have 1to1 mapping.
    # e.g.: shuffling of keys, indentation, etc.
    # need standards to "canonicalize" HistoryList json for hashing reasons
    # e.g.: 
    # 1. no indent for History jsons
    # 2. list needs to be sorted in some order
    # 3. need to use "," separators
    # .....
    # However this shouldn't be a problem if client stores the exact json it received?
    def to_json(self):
        history_dict_list = [hist.to_dict() for hist in self.entries]
        result_dict = {self.obj_id: history_dict_list}
        return json.dumps(result_dict)
    
    def to_dict(self):
        history_dict_list = [hist.to_dict() for hist in self.entries]
        result_dict = {self.obj_id: history_dict_list}
        return result_dict

    # get hash of a list of histories
    def to_hash(self):
        result = hashlib.sha256(self.to_json().encode()).hexdigest()
        return result
    

