'''
@File    :   time_sync.py
@Time    :   2026/03/11
@Author  :   @ximing
@Version :   1.0
@Desc    :   Time Synchronization Wrapper for QuecPython
'''

import utime
import ntptime
from usr.logger import Logger, DEBUG, INFO

log = Logger("TimeSync", log_dir="/usr", level=DEBUG)

class TimeSync:
    def __init__(self, ntp_server="pool.ntp.org", time_zone=8):
        self.ntp_server = ntp_server
        self.time_zone = time_zone
        self.last_sync_time = 0

    def sync(self):
        try:
            ntptime.sethost(self.ntp_server)
            utime.setTimeZone(self.time_zone)
            ntptime.settime()
            self.last_sync_time = utime.time()
            log.info("Sync success, time: {}".format(utime.localtime()))
        except Exception as e:
            log.error("Sync failed:", e)

timesync = TimeSync()