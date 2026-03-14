import log
import utime
import uos

DEBUG    = log.DEBUG
INFO     = log.INFO
WARNING  = log.WARNING
ERROR    = log.ERROR
CRITICAL = log.CRITICAL

class Logger:
    def __init__(self, name, log_dir="/usr", max_size=24*1024, max_files=2, level=INFO, save_to_file=True):
        self.name              = name
        self.log_dir           = log_dir
        self.max_size          = max_size
        self.max_files         = max_files
        self.level             = level
        self.save_to_file_flag = save_to_file
        self.current_log_file  = None
        
        log.basicConfig(level=self.level)
        self._sys_log = log.getLogger(name)
        
        # Initialize current log file
        self._check_file()

    def set_level(self, level):
        self.level = level
        log.basicConfig(level=level)

    def _get_new_log_filename(self):
        # Format: system_YYYYMMDD_HHMMSS.log
        t = utime.localtime()
        # Using a consistent prefix to easily identify and rotate logs
        return "{}/system_{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}.log".format(
            self.log_dir, t[0], t[1], t[2], t[3], t[4], t[5]
        )

    def _rotate_logs(self):
        try:
            # Get all log files in directory starting with "system_" and ending with ".log"
            files = [f for f in uos.listdir(self.log_dir) if f.startswith("system_") and f.endswith(".log")]
            # Sort by name (which contains timestamp, so effectively by date)
            files.sort()
            
            # Remove oldest files if we exceed the limit
            # We want to keep (max_files - 1) because we are about to create a new one
            while len(files) >= self.max_files:
                oldest = files.pop(0)
                try:
                    uos.remove(self.log_dir + "/" + oldest)
                except:
                    pass
        except Exception as e:
            print("[Logger Error] Rotation failed:", e)

    def _check_file(self):
        # If we already have a current file, check its size
        if self.current_log_file:
            try:
                size = uos.stat(self.current_log_file)[6]
                if size < self.max_size:
                    return # Current file is still good
            except OSError:
                # File might have been deleted or error accessing it
                pass
        
        # Need to select or create a file
        try:
            files = [f for f in uos.listdir(self.log_dir) if f.startswith("system_") and f.endswith(".log")]
            files.sort()
            
            if files:
                latest = files[-1]
                latest_path = self.log_dir + "/" + latest
                try:
                    size = uos.stat(latest_path)[6]
                    if size < self.max_size:
                        self.current_log_file = latest_path
                        return
                except:
                    pass
        except:
            pass
            
        # Create new file (rotate first)
        self._rotate_logs()
        self.current_log_file = self._get_new_log_filename()

    def _write_to_file(self, level_name, msg):
        if not self.save_to_file_flag:
            return
            
        try:
            self._check_file()
            
            local_time = utime.localtime()
            timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                local_time[0], local_time[1], local_time[2],
                local_time[3], local_time[4], local_time[5]
            )
            
            # Format: [Timestamp] [Level] [Name] Message
            log_entry = "[{}] [{}] [{}] {}\n".format(timestamp, level_name, self.name, msg)
            
            with open(self.current_log_file, "a+") as f:
                f.write(log_entry)
        except Exception as e:
            print("[Logger Error] Failed to write to file:", e)

    def debug(self, msg):
        self._sys_log.debug(msg)
        if self.level <= DEBUG:
            self._write_to_file("DEBUG", msg)

    def info(self, msg):
        self._sys_log.info(msg)
        if self.level <= INFO:
            self._write_to_file("INFO", msg)

    def warning(self, msg):
        self._sys_log.warning(msg)
        if self.level <= WARNING:
            self._write_to_file("WARNING", msg)

    def error(self, msg):
        self._sys_log.error(msg)
        if self.level <= ERROR:
            self._write_to_file("ERROR", msg)

    def critical(self, msg):
        self._sys_log.critical(msg)
        if self.level <= CRITICAL:
            self._write_to_file("CRITICAL", msg)
