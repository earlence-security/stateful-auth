# defines a list of history objects
# maxlen(list) = number of apis able to access this object

import time
import json
from .history import History
import hashlib

# Server         : Store (new HistoryList -> json -> hash)
# Server response: new HistoryList -> json -> Client
# Client request : json -> Server
# Server         : json -> hash ==? stored hash
# Server         : json -> HistoryList -> add new history -> new HistoryList
# repeat
class HistoryList:

    def __init__(self, json_str=None):
        self.entries = []
        if json_str != None:
            history_list_dict = json.loads(json_str)
            history_dict_list = history_list_dict["history"]
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
        result_dict = {"history": history_dict_list}
        return json.dumps(result_dict)


    # get hash of a list of histories
    def to_hash(self):
        result = hashlib.sha256(self.to_json().encode()).hexdigest()
        return result
    

# sample usage
if __name__ == "__main__":
    h1 = History(api="http://127.0.0.1:5000/api/send-money", method="POST")
    print(h1)

    h2 = History(api="http://127.0.0.1:5000/api/emails", method="GET")
    print(h2)

    time.sleep(0.1)

    h3 = History(api="http://127.0.0.1:5000/api/emails", method="GET")
    print(h3)

    hlist = HistoryList()
    hlist.append(h1)
    print(hlist)
    hlist.append(h2)
    print(hlist)
    hlist.append(h3)
    print(hlist)


    hlhash = hlist.to_hash()
    print(hlhash)

    hlreconstruct = HistoryList(hlist.to_json())
    print(hlreconstruct)

    hlreconstructhash = hlreconstruct.to_hash()
    print(hlreconstructhash)