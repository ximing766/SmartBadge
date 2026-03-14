'''
@File    :   network_manager.py
@Time    :   2026/03/07
@Author  :   @ximing
@Version :   2.0 (Simplified)
'''

import checkNet
import dataCall
import utime
import usocket
import net
from misc import Power
from usr.logger import Logger, DEBUG, INFO, WARNING, ERROR
from umqtt import MQTTClient
from aLiYun import aLiYun
import checkNet

log = Logger("NetMgr", log_dir="/usr", level=DEBUG)

class AliyunIotClient:
    def __init__(self, product_key, product_secret=None, device_name=None, device_secret=None):
        self.product_key    = product_key
        self.product_secret = product_secret
        self.device_name    = device_name
        self.device_secret  = device_secret
        self.ali            = None

    def connect(self, client_id="", keep_alive=300):
        try:
            self.ali = aLiYun(self.product_key, self.product_secret, self.device_name, self.device_secret)
            
            # Use device_name as client_id if not provided
            if not client_id:
                client_id = self.device_name
                
            ret = self.ali.setMqtt(client_id, clean_session=False, keepAlive=keep_alive)
            if ret != 0:
                log.error("Failed to set MQTT parameters (ret={})".format(ret))
                return False
                
            self.ali.error_register_cb(self._error_cb)
            self.ali.start()
            log.info("Aliyun IoT Client started")
            return True

        except Exception as e:
            log.error("Aliyun connect error: {}".format(e))
            return False

    def disconnect(self):
        if self.ali:
            self.ali.disconnect()
            log.info("Aliyun IoT Client disconnected")

    def set_callback(self, callback):
        if self.ali:
            self.ali.setCallback(callback)

    def subscribe(self, topic):
        if self.ali:
            self.ali.subscribe(topic)
            log.info("Subscribed to topic: {}".format(topic))

    def publish(self, topic, msg):
        if self.ali:
            self.ali.publish(topic, msg)
            log.info("Published to topic: {}".format(topic))

    def _error_cb(self, err):
        log.error("Aliyun internal error: {}".format(err))


ALI_PRODUCT_KEY     = "a1VbNdXKNCE"
ALI_PRODUCT_SECRET  = None    # fwODz2DJcAIj635d
ALI_DEVICE_NAME     = "SZ_Device_1"
ALI_DEVICE_SECRET   = "7a8c2b6f390a1ec48f8cf80f83ed5986"   # 7a8c2b6f390a1ec48f8cf80f83ed5986
ALI_TOPIC_PROP_POST = "/sys/{}/{}/thing/event/property/post".format(ALI_PRODUCT_KEY, ALI_DEVICE_NAME)

ali_client          = AliyunIotClient(ALI_PRODUCT_KEY, ALI_PRODUCT_SECRET, ALI_DEVICE_NAME, ALI_DEVICE_SECRET)


class NetworkManager:
    def __init__(self, profile_idx=1):
        self.profile_idx = profile_idx
        self.apn         = None

    def detect_apn(self):
        for _ in range(3):
            try:
                # net.operatorName() might return -1 or raise exception if SIM not ready
                op_info = net.operatorName() # ('CHINA MOBILE', 'CMCC', '460', '00')
                if op_info != -1 and op_info and op_info[0]:
                    mcc = op_info[2]
                    mnc = op_info[3]
                    log.info("Operator: {} (MCC:{}, MNC:{})".format(op_info[0], mcc, mnc))
                    
                    if mcc == '460': # China
                        if mnc in ['00', '02', '04', '07']: return "cmnet"
                        elif mnc in ['01', '06', '09']: return "3gnet"
                        elif mnc in ['03', '05', '11']: return "ctnet"
                    return "cmnet" # Default fallback
            except Exception as e:
                log.warning("Operator detection error: {}".format(e))
            utime.sleep(1)
        
        log.warning("Could not detect operator (SIM missing?)")
        return "unknown"

    def check_and_config_apn(self):
        target_apn = self.detect_apn()
        if target_apn == 'unknown':
            return False
        
        # getPDPContext(profileID) -> [ip_type, apn, user, pwd, auth]
        pdp_ctx = dataCall.getPDPContext(self.profile_idx)
        
        current_apn = ""
        if pdp_ctx != -1 and isinstance(pdp_ctx, (list, tuple)):
            current_apn = pdp_ctx[1]
            
        log.info("Target APN: {}, Current APN: {}".format(target_apn, current_apn))
        
        if current_apn != target_apn:
            log.warning("APN Mismatch! Configuring to {}...".format(target_apn))
            # setPdpContext(profile_idx, ip_type=0(IPv4), apn, user, pwd, auth)
            ret = dataCall.setPdpContext(self.profile_idx, 0, target_apn, "", "", 0)
            if ret == 0:
                log.warning("APN set successfully. System RESTARTING in 3s to apply...")
                utime.sleep(3)
                Power.powerRestart()
                return True # Should not reach here
            else:
                log.error("Failed to set APN.")
                return False
        
        log.info("APN Config OK.")
        return True

    def wait_for_network(self, timeout=60):
        log.info("Waiting for network (checkNet) up to {}s...".format(timeout))
        
        stage, state = checkNet.waitNetworkReady(timeout)
        
        if stage == 3 and state == 1:
            log.info("Network Connected Successfully.")
            pdp_info = dataCall.getInfo(self.profile_idx, 0)
            if pdp_info != -1 and pdp_info[2][0] == 1:
                log.info("IP Address: {}".format(pdp_info[2][2]))
            return True
        else:
            log.error("Network check failed. Stage: {}, State: {}".format(stage, state))
            return False

    def test_connectivity(self):
        log.info("Testing Connectivity (HTTP GET)...")
        host = 'python.quectel.com'
        port = 80
        sock = None
        try:
            # 1. DNS Resolution
            log.debug("Resolving DNS for {}...".format(host))
            addr_info = usocket.getaddrinfo(host, port)
            server_addr = addr_info[0][-1]
            log.debug("Resolved: {}".format(server_addr))

            # 2. Create Socket
            sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
            sock.settimeout(10) # 10s timeout

            # 3. Connect
            log.debug("Connecting...")
            sock.connect(server_addr)
            
            # 4. Send Request
            request = 'GET /News HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n'.format(host)
            sock.send(request)
            
            # 5. Receive Response
            data = sock.recv(128)
            if data:
                log.info("Received {} bytes. Test PASSED.".format(len(data)))
                log.debug("Response snippet: {}".format(data[:50]))
                return True
            else:
                log.warning("No data received.")
                return False

        except Exception as e:
            log.error("Connectivity Test Failed: {}".format(e))
            return False
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass

net_mgr = NetworkManager()


def connect():
    # 1. Check and Auto-Config APN first
    # This might cause a restart if APN changes
    if not net_mgr.check_and_config_apn():
        return False

    # 2. Wait for network ready (checkNet)
    if not net_mgr.wait_for_network(60):
        return False
    
    # 3. Run a quick connectivity test
    # return net_mgr.test_connectivity()
    return True
