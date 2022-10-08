import os
import time
import traceback
from typing import Any, Tuple

class Logging:
    def __init__(self, suffix: str = "logs"):
        self.cwd = os.getcwd()    
        self.suffix = suffix

        self.time_string = time.strftime("%d-%m-%Y")

        if not os.path.exists(f"{self.cwd}/logs"):
            os.mkdir(f"{self.cwd}/logs")
        
    def check_time_date(self):
        now = time.strftime("%d-%m-%Y")
        if now != self.time_string:
            self.log("[#] The date has changed, using new log file...", True, False)
            self.time_string = now


    def log(self, msg: str, console = True, check_date = True):
        if check_date:
            self.check_time_date()

        if console:
            print(f"[{time.strftime('%H:%M:%S')}]" f" {msg.encode('ascii', 'replace').decode()}")

        with open(f"logs/{self.suffix}-{self.time_string}.log", "a") as logfile:
            logfile.write(f"[{time.strftime('%d-%m-%Y %H:%M:%S')}]" f" {msg.encode('ascii', 'replace').decode()}\n")
    
    def exception(self, type : type[BaseException], msg: str, tb: traceback):
        self.suffix = "exceptions"

        trace_back = traceback.extract_tb(tb)

        self.log("An exception occured: ")
        self.log(f"Exception type : {type.__name__}", True, False)
        self.log(f"Exception message : {msg}", True, False)
        self.log(f"Stack trace :", False, False)
        for trace in trace_back:
            self.log(f"\t - File : {trace[0]} , Line : {trace[1]}, Function : {trace[2]}, Message : {trace[3]}", False, False)

    def clear_logs(self):
        for f in os.listdir(f"{self.cwd}/logs"):
            if os.path.isfile(f"{self.cwd}/logs/{f}"):
                os.remove(f"{self.cwd}/logs/{f}")

