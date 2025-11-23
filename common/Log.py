import os
import datetime

class Log:
    def __init__(self, base_name, debug_mode=False):
        self.debug_mode = debug_mode
        self.LOG_BASE_NAME = os.getcwd() + base_name
        print(f"LOG_BASE_NAME {self.LOG_BASE_NAME}")
        if os.path.isfile(self.LOG_BASE_NAME + '3.log'):
            os.remove(self.LOG_BASE_NAME + '3.log')
        if os.path.isfile(self.LOG_BASE_NAME + '2.log'):
            os.rename(self.LOG_BASE_NAME + '2.log', self.LOG_BASE_NAME + '3.log')
        if os.path.isfile(self.LOG_BASE_NAME + '1.log'):
            os.rename(self.LOG_BASE_NAME + '1.log', self.LOG_BASE_NAME + '2.log')
        if os.path.isfile(self.LOG_BASE_NAME + '.log'):
            os.rename(self.LOG_BASE_NAME + '.log', self.LOG_BASE_NAME + '1.log')
        print(f"log {self.LOG_BASE_NAME + '.log'}")
        self.log = open(self.LOG_BASE_NAME + '.log', 'w', encoding='utf-8')
    def put(self, msg):
        now = datetime.datetime.now()
        msg = f"[{now.strftime('%y/%m/%d %H:%M:%S')}]{msg}\n"
        self.log.write(msg)
        self.log.flush()
    def debug(self, msg):
        if self.debug_mode == False:
            return
        self.put(f"[DEBUG] {msg}")
