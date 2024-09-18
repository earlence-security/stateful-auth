# defines a list of historylist to send over wire

import time
import ujson as json
from .history import History
from .history_list import HistoryList
import hashlib

# {
#   obj_id1 : [history_entry1, history_entry2, ...]
#   obj_id2 : [history_entry1, history_entry2, ...]
#   .........
# }
class BatchHistoryList:

    def __init__(self, historylists=None, json_str=None):
        # A dict of (obj_id, historylist)
        self.entries = {}
        if historylists and len(historylists) > 0:
            if isinstance(historylists[0], HistoryList):
                for historylist in historylists:
                    self.entries[historylist.obj_id] = historylist
            else:
                raise ValueError("historylists should be a list of HistoryList objects")
        elif json_str is not None:
            bhl_dict = json.loads(json_str)
            for obj_id, historylist_dict in bhl_dict.items():
                currHistoryList = HistoryList(obj_id, json.dumps(historylist_dict))
                self.entries[obj_id] = currHistoryList


    def __str__(self):
        return "BatchHistoryList: " + self.to_json()


    def append(self, obj_id, history: History):
        if obj_id in self.entries:
            old_histlist = self.entries[obj_id]
            old_histlist.append(history)
            self.entries[obj_id] = old_histlist


    def to_json(self):
        entries_dict = {}
        for k, v in self.entries.items():
            entries_dict.update({k: v.to_dict()})
        return json.dumps(entries_dict)
    
    def get_num_objects(self):
        """Number of objects in the batch history list."""
        return len(self.entries)
    
    def get_num_history_entries(self):
        """Length of history entries in the batch history list."""
        return sum([len(v.entries) for _, v in self.entries.items()])


# sample useage
if __name__ == "__main__":

    h1 = History(api="http://127.0.0.1:5000/api/send-money", method="POST")
    h2 = History(api="http://127.0.0.1:5000/api/emails", method="GET")
    time.sleep(0.1)
    h3 = History(api="http://127.0.0.1:5000/api/emails", method="GET")

    hlist = HistoryList(obj_id="asdf")
    hlist.append(h1)
    hlist.append(h2)
    hlist.append(h3)
    print(hlist)

    h4 = History(api="http://127.0.0.1:5000/api/hello", method="DELETE")
    h5 = History(api="http://127.0.0.1:5000/api/emails", method="GET")
    time.sleep(0.5)
    h6 = History(api="http://127.0.0.1:5000/api/emails", method="GET")

    hlist2 = HistoryList(obj_id="hello")
    hlist2.append(h4)
    hlist2.append(h5)
    hlist2.append(h6)
    print(hlist2)

    b = BatchHistoryList([hlist, hlist2])
    print(b)

    breconstruct = BatchHistoryList(json_str=b.to_json())
    print(breconstruct)
