'''
@File    :   main.py
@Time    :   2026/03/07
@Author  :   @ximing
@Version :   1.0
'''

import utime
import _thread
import sim

from usr.logger import Logger, DEBUG, INFO, WARNING, ERROR, CRITICAL
import usr.basic as basic
import usr.audio_recorder as audio_rec
import usr.network_manager as net_mgr
import usr.pm_manager as pm_mgr
import usr.time_sync as time_sync
import ujson
import app_fota
from misc import Power

log = Logger("Main", log_dir="/usr", level=DEBUG)

def perform_ota_update():
    log.info("Starting OTA Update...")
    
    base_url = "https://gitee.com/ximing766/SmartBadge/raw/main/Code/"
    
    file_list = [
        {'file_name': '/usr/main.py', 'url': base_url + 'main.py'},
        {'file_name': '/usr/basic.py', 'url': base_url + 'basic.py'},
        {'file_name': '/usr/pm_manager.py', 'url': base_url + 'pm_manager.py'},
        {'file_name': '/usr/network_manager.py', 'url': base_url + 'network_manager.py'},
        {'file_name': '/usr/logger.py', 'url': base_url + 'logger.py'},
        {'file_name': '/usr/time_sync.py', 'url': base_url + 'time_sync.py'}
    ]
    try:
        fota = app_fota.new()
        log.info("Downloading files from: {}".format(base_url))
        
        fota.bulk_download(file_list)  # batch download
        
        log.info("Download complete. Setting update flag...")
        fota.set_update_flag()
        
        log.warning("System RESTARTING for update...")
        utime.sleep(2)
        Power.powerRestart()
        
    except Exception as e:
        log.error("OTA Update Failed: {}".format(e))

def s2_handler(pin):
    log.info("Button S2 Pressed!")
    basic.d4.on()
    perform_ota_update()
    basic.d4.off()

    # pm_mgr.pm_mgr.lock("recording")
    # audio_rec.recorder.start_record()
    

def s3_handler(pin):
    log.info("Button S3 Pressed!")
    basic.d3.blink()
    # if audio_rec.recorder.is_recording:
    #     audio_rec.recorder.stop_record()
    #     pm_mgr.pm_mgr.unlock("recording")
    # else:
    #     audio_rec.recorder.play_recording()

def get_aliyun_payload(power=100, status=1):
    return {
        "id": str(utime.ticks_ms()),
        "version": "1.0",
        "params": {
            "Power": power,
            "Status": status
        },
        "method": "thing.event.property.post"
    }

# Global Variables
ali_timer = None
mqtt_publish_flag = False

def mqtt_timer_handler(args):
    if net_mgr.ali_client and net_mgr.ali_client.ali:

        payload = get_aliyun_payload()
        msg = ujson.dumps(payload)
        
        try:
            net_mgr.ali_client.publish(net_mgr.ALI_TOPIC_PROP_POST, msg)
        except Exception as e:
            log.error("MQTT Publish Error: {}".format(e))

def hardware_init():
    global ali_timer
    log.info("Initializing Hardware...")
    
    # System Info
    try:
        sys_info = basic.INFO("FW_20260311")
        log.info("Version: {}".format(sys_info.get_version()))
        log.info("System Info: {}".format(sys_info.get_core_info()))
    except Exception as e:
        log.error("Failed to get system info: {}".format(e))
    
    utime.sleep_ms(100)
    
    try:
        if net_mgr.connect():
            if net_mgr.ali_client.connect():
                log.info("Aliyun IoT Connected Successfully")
                # Keep reference to the timer to prevent GC
                ali_timer = basic.create_timer(mqtt_timer_handler, 10000, periodic=True)  # 10s
            else:
                log.error("Aliyun IoT Connect Failed")
        else:
            log.error("Network Configuration: Failed")
    except Exception as e:
        log.error("Network Configuration Exception: {}".format(e))
    
    # 使能sim卡热插拔
    sim.setSimDet(1, 1)

    time_sync.timesync.sync_time()

    # Enable Auto Sleep
    # pm_mgr.pm_mgr.enable_autosleep(False)
    
    basic.init_buttons(s2_handler, s3_handler)

def app_main():
    try:
        hardware_init()
        while True:
            # log.info("System Heartbeat")
            utime.sleep(5) 
        
    except Exception as e:
        log.critical("Unhandled Exception: {}".format(e))

if __name__ == "__main__":
    app_main()
