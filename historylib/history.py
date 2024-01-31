# defines a single history data point

import time
import orjson as json

class History:

    def __init__(self, api, method, counter=0, timestamp=None):
        self.api = api
        self.method = method
        self.counter = counter
        if timestamp == None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp

    
    @classmethod
    def from_dict(cls, history_dict):
        api = history_dict["api"]
        method = history_dict["method"]
        counter = history_dict["counter"]
        timestamp = history_dict["timestamp"]
        return cls(api, method, counter, timestamp)


    def __str__(self):
        return "History: " + self.to_json()


    def to_dict(self):
        history_dict = {
            "api": self.api,
            "method": self.method,
            "counter": self.counter,
            "timestamp": self.timestamp
        }
        return history_dict


    def to_json(self):
        history_dict = self.to_dict()
        history_json = json.dumps(history_dict)
        return history_json

    