'''
@File    :   basic.py
@Time    :   2026/03/07
@Author  :   @ximing
@Version :   1.0
'''

from machine import Pin, ExtInt
import utime
import uos
import gc
import modem
import sim
from misc import Power
import osTimer

D3_PIN_NUM = Pin.GPIO21 
D4_PIN_NUM = Pin.GPIO22 
S2_PIN_NUM = ExtInt.GPIO46
S3_PIN_NUM = ExtInt.GPIO45

def create_timer(callback, interval_ms, periodic=True):
    timer = osTimer()
    mode = 1 if periodic else 0
    timer.start(interval_ms, mode, callback)
    return timer

def stop_timer(timer):
    if timer:
        timer.stop()

class INFO:
    def __init__(self, version="FW_20260309"):
        self.version = version
    
    def get_version(self):
        return self.version
    
    def get_imei(self):
        try:
            return modem.getDevImei()
        except:
            return "Unknown"

    def get_iccid(self):
        try:
            return sim.getIccid()
        except:
            return "Unknown"

    def get_vbatt(self):   # voltage in mV
        try:
            return Power.getVbatt()
        except:
            return -1

    def get_storage_free_kb(self, path='/usr'):
        try:
            stat = uos.statvfs(path)
            # stat[0] = f_bsize, stat[3] = f_bfree
            return (stat[0] * stat[3]) // 1024
        except:
            return -1

    def get_ram_free_kb(self):
        try:
            return gc.mem_free() // 1024
        except:
            return -1

    def get_core_info(self):
        return {
            "IMEI": self.get_imei(),
            "ICCID": self.get_iccid(),
            "Free_USR_KB": self.get_storage_free_kb('/usr'),
            "Free_BAK_KB": self.get_storage_free_kb('/bak'),
            "Free_RAM_KB": self.get_ram_free_kb()
        }

class LED:
    def __init__(self, pin_num):
        self.pin = Pin(pin_num, Pin.OUT, Pin.PULL_DISABLE, 0)
        self.state = 0
        self.off() # Initialize off

    def on(self):
        self.pin.write(1)
        self.state = 1

    def off(self):
        self.pin.write(0)
        self.state = 0

    def toggle(self):
        self.state = 1 - self.state
        self.pin.write(self.state)
        
    def blink(self, interval_ms=500):
        self.on()
        utime.sleep_ms(interval_ms)
        self.off()
        utime.sleep_ms(interval_ms)

class Button:
    def __init__(self, pin_num, callback, trigger=ExtInt.IRQ_FALLING, pull=ExtInt.PULL_PU):
        self.pin_num = pin_num
        self.callback = callback
        # ExtInt callback receives args
        self.extint = ExtInt(pin_num, trigger, pull, self._internal_callback, filter_time=50)
        self.extint.enable()

    def _internal_callback(self, args):
        if self.callback:
            # Pass pin number to callback
            self.callback(self.pin_num)

    def enable(self):
        self.extint.enable()

    def disable(self):
        self.extint.disable()

# Initialize global LED instances
d3 = LED(D3_PIN_NUM)
d4 = LED(D4_PIN_NUM)

# Button helpers
def init_buttons(s2_cb=None, s3_cb=None):
    s2 = None
    s3 = None
    if s2_cb:
        s2 = Button(S2_PIN_NUM, s2_cb)
    if s3_cb:
        s3 = Button(S3_PIN_NUM, s3_cb)
    return s2, s3
