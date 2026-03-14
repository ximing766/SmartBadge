'''
@File    :   pm_manager.py
@Time    :   2026/03/11
@Author  :   @ximing
@Version :   1.0
@Desc    :   Power Management Wrapper for QuecPython
'''

import pm
import utime
from usr.logger import Logger, DEBUG, INFO

log = Logger("PM", log_dir="/usr", level=DEBUG)

class PowerManager:
    def __init__(self):
        self.wakelocks = {} # Dictionary to store wakelock IDs: {name: id}
        
    def enable_autosleep(self, enable=True):
        flag = 1 if enable else 0
        ret = pm.autosleep(flag)
        if ret == 0:
            log.info("Auto-sleep set to: {}".format("Enabled" if enable else "Disabled"))
            return True
        else:
            log.error("Failed to set auto-sleep mode")
            return False

    def create_wakelock(self, name):
        if name in self.wakelocks:
            log.warning("Wakelock '{}' already exists.".format(name))
            return self.wakelocks[name]
        
        lock_id = pm.create_wakelock(name, len(name))
        if lock_id >= 0:
            self.wakelocks[name] = lock_id
            log.info("Created wakelock: {} (ID: {})".format(name, lock_id))
            return lock_id
        else:
            log.error("Failed to create wakelock: {}".format(name))
            return -1

    def delete_wakelock(self, name):
        if name in self.wakelocks:
            lock_id = self.wakelocks[name]
            ret = pm.delete_wakelock(lock_id)
            if ret == 0:
                del self.wakelocks[name]
                log.info("Deleted wakelock: {}".format(name))
                return True
            else:
                log.error("Failed to delete wakelock: {}".format(name))
                return False
        else:
            log.warning("Wakelock '{}' not found.".format(name))
            return False

    def lock(self, name):
        if name not in self.wakelocks:
            # Auto-create if not exists
            if self.create_wakelock(name) == -1:
                return False
        
        lock_id = self.wakelocks[name]
        ret = pm.wakelock_lock(lock_id)
        if ret == 0:
            log.debug("Acquired lock: {}".format(name))
            return True
        else:
            log.error("Failed to acquire lock: {}".format(name))
            return False

    def unlock(self, name):
        if name in self.wakelocks:
            lock_id = self.wakelocks[name]
            ret = pm.wakelock_unlock(lock_id)
            if ret == 0:
                log.debug("Released lock: {}".format(name))
                return True
            else:
                log.error("Failed to release lock: {}".format(name))
                return False
        else:
            log.warning("Wakelock '{}' not found.".format(name))
            return False
            
    def get_wakelock_count(self):
        return pm.get_wakelock_num()

# Global instance
pm_mgr = PowerManager()

