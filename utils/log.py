import os
import json
from dataclasses import dataclass
from datetime import datetime


@dataclass 
class RequestLog:
    """A dataclass for storing request logs."""
    # Request metadata
    request_path: str
    request_method: str
    policy_hash: str = ""
    policy_succeeds: bool = False
    # Request parameters
    request_size: int = 0
    request_data_size: int = 0
    history_length: int = 0
    history_size: int = 0
    # Response parameters
    response_data_size: int = 0
    # Latency info
    request_total_time: float = 0.0
    token_validation_time: float = 0.0
    history_validation_time: float = 0.0
    policy_execution_time: float = 0.0
    history_update_time: float = 0.0    # Time to update the history hash value in the database
    resource_api_time: float = 0.0

    def __str__(self):
        return f"RequestLog: {self.__dict__}"

    def __repr__(self):
        return self.__str__()
    
    def to_dict(self):
        return self.__dict__
    
    def to_json(self):
        return json.dumps(self.__dict__)

class LogManager:
    """A manager class for storing request logs.
    
    Attributes:
        logs: (list[RequestLog]) A list of past logs for the requests that have been processed
    """
    def __init__(self):
        self.logs: list[RequestLog] = []

    def add_log(self, log):
        self.logs.append(log)

    def get_logs(self):
        return self.logs

    def clear_logs(self):
        self.logs = []
    
    def print_all_logs(self):
        print(f"[LOGGING] {self.logs}")

    def __str__(self):
        return f"LogManager: {self.__dict__}"

    def __repr__(self):
        return self.__str__()
    
    def to_file(self):
        """Write the logs to a file."""
        if not os.path.exists("logs"):
            os.makedirs("logs")
        log_list = [log.to_dict() for log in self.logs]
        suffix = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        with open(f"logs/logs_{suffix}.txt", "w") as f:
            f.write(json.dumps(log_list, indent=2))
