import json

id = "id:a4ayc_80_OEAAAAAAAAAXz"
fake_history_entries_folder = [
    {
        "api": "/files/create_folder_v2",    # get
        "method": "POST",
        "counter": 0,
        "timestamp": 1705279436.833235
    },
    {
        "api": "/files/list_folder",    # import
        "method": "POST",
        "counter": 0,
        "timestamp": 1705279436.833235
    },
    {
        "api": "/files/list_folder/continue",          # insert
        "method": "POST",
        "counter": 0,
        "timestamp": 1705279436.833235
    },
    {
        "api": "/files/get_metadata",          # instances
        "method": "POST",
        "counter": 0,
        "timestamp": 1705279436.833235
    }
]
fake_history_entries_file = [
    {
        "api": "/files/upload",          # list
        "method": "POST",
        "counter": 0,
        "timestamp": 1705279436.833235
    },
    {
        "api": "/files/download",          # move
        "method": "POST",
        "counter": 0,
        "timestamp": 1705279436.833235
    },
    {
        "api": "/files/get_metadata",          # instances
        "method": "POST",
        "counter": 0,
        "timestamp": 1705279436.833235
    }
]
history = {id: fake_history_entries_folder}
print(json.dumps(history))
print(len(json.dumps(history)))