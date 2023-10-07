from .history import History
from .history_list import HistoryList
import os

def history_to_file(history_list: HistoryList, filename, path):
    history_json = history_list.to_json()
    file_path = os.path.join(path, filename)  

    with open(file_path, "w") as outfile:
        outfile.write(history_json)


# get historyList from directory storing history json files, if not found return None
def get_history(filename, directory):
    file_path = os.path.join(directory, filename)

    if not os.path.isfile(file_path):
        return None
    
    with open(file_path, "r") as infile:
        history_json = infile.read()
        history_list = HistoryList(history_json)
        return history_list

