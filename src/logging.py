import os
import time
import glob
import shutil
import traceback
class Logging:
    def __init__(self, cfg, suffix: str = "logs"):
        self.cwd = os.getcwd()    
        self.suffix = suffix
        self.cfg = cfg

        self.time_string = time.strftime("%d-%m-%Y")

        if not os.path.exists(f"{self.cwd}/logs"):
            os.mkdir(f"{self.cwd}/logs")
            
        self.check_time_date()

    def check_time_date(self):
        now = time.strftime("%d-%m-%Y")

        (day, month, year) = now.split("-")
        (old_day, old_month, old_year) = self.time_string.split("-")
        
        if day != old_day:
            self.log("[#] The day has changed, using new log file...", True, False)
            self.time_string = now
            
        if month != old_month:
            self.log("[#] The month has changed, moving all files from the past month into a folder...", True, False)
            
            files = glob.glob(f"logs/*.log")
            for file in files:
                (log_type, log_day, log_month, log_year) = file.replace(".log", "").split("-")
                if not os.path.exists(f"logs/{log_year}"):
                    os.mkdir(f"logs/{log_year}/")
                    
                if not os.path.exists(f"logs/{log_year}/{log_month}"):
                    os.mkdir(f"logs/{log_year}/{log_month}")

                shutil.move(file, f"logs/{log_year}/{log_month}")    
                
            for dir in glob.glob("logs/*"):
                if os.path.isdir(dir):
                    for sub_dir in glob.glob(f"{dir}/*"):
                        if os.path.isdir(dir):
                            (_, year, month) = sub_dir.split("\\")
                            shutil.make_archive(f"{dir}/{month}", "zip", sub_dir)
                            shutil.rmtree(f"{dir}/{month}")
                    
            self.time_string = now


    def log(self, msg: str, console = True, check_date = True):
        if check_date:
            self.check_time_date()

        if console:
            print(f"[{time.strftime('%H:%M:%S')}] {msg.encode('ascii', 'replace').decode()}")

        with open(f"logs/{self.suffix}-{self.time_string}.log", "a") as logfile:
            logfile.write(f"[{time.strftime('%d-%m-%Y %H:%M:%S')}] {msg.encode('ascii', 'replace').decode()}\n")
    
    def exception(self, type : BaseException, msg: str, tb: traceback):
        self.suffix = "exceptions"

        trace_back = traceback.extract_tb(tb)

        self.log("An exception occured: ")
        self.log(f"Exception type : {type.__name__}", True, False)
        self.log(f"Exception message : {msg}", True, False)
        self.log(f"Stack trace :", self.cfg.DEBUG, False)
        for trace in trace_back:
            self.log(f"\t - File : {trace[0]} , Line : {trace[1]}, Function : {trace[2]}, Message : {trace[3]}", self.cfg.DEBUG, False)

    def clear_logs(self):
        for f in os.listdir(f"{self.cwd}/logs"):
            if os.path.isfile(f"{self.cwd}/logs/{f}"):
                os.remove(f"{self.cwd}/logs/{f}")

