from dataclasses import dataclass


@dataclass 
class RequestLog:
    """A dataclass for storing request logs."""
    # Request metadata
    request_path: str
    request_method: str
    policy_hash: str = ""
    # Request parameters
    request_data_size: int = 0
    history_length: int = 0
    history_size: int = 0
    # Response parameters
    response_data_size: int = 0
    # Latency info
    token_validation_time: float = 0.0
    history_validation_time: float = 0.0
    policy_execution_time: float = 0.0
    history_update_time: float = 0.0    # Time to update the history hash value in the database

    def __str__(self):
        return f"RequestLog: {self.__dict__}"

    def __repr__(self):
        return self.__str__()

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
        with open("logs.txt", "w") as f:
            for log in self.logs:
                f.write(str(log) + "\n")
