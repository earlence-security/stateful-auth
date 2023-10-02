from historylib.history import History

# get hash of a list of histories
# this could be tricky because json to string don't have a guaranteed representation.
# e.g.: shuffling of keys, indentation, etc.
def generate_history_hash(history_list, hash_algo):
    return