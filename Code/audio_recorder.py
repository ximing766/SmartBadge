'''
@File    :   audio_recorder.py
@Time    :   2026/03/07
@Author  :   @ximing
@Version :   1.0
'''

import audio
import utime
import uos
import _thread
from usr.logger import Logger, DEBUG, INFO
import usr.basic as basic

log = Logger("Audio", log_dir="/usr", level=DEBUG)

class AudioRecorder:
    def __init__(self):
        # try:
        #     self.aud = audio.Audio(2)
        #     self.aud.setVolume(11) # Set default volume
        # except Exception as e:
        #     log.error("Failed to init Audio playback: {}".format(e))
        #     self.aud = None
        self.aud = None
        try:
            self.record = audio.Record(0) # 0 for MIC usually
        except Exception as e:
            log.error("Failed to init Audio record: {}".format(e))
            self.record = None

        self.is_recording = False
        self.record_file = "/usr/record_test.wav"
        
        if self.record:
            self.record.end_callback(self._record_callback)

    def _record_callback(self, args):
        # args: [file_name, file_size, record_status]
        # record_status: 3=Finished, -1=Failed
        file_name = args[0]
        file_size = args[1]
        record_sta = args[2]
        
        log.info("Record CB: Name={}, Size={}, Status={}".format(file_name, file_size, record_sta))
        
        # record_sta: 0=Start, 3=Finished, -1=Failed
        if record_sta == 0:
            log.info("Recording started callback.")
            return

        self.is_recording = False
        basic.d3.off() # Turn off recording LED
        
        if record_sta == 3:
            log.info("Recording finished successfully.")
            # Automatically play back the recording
            self.play_recording()
        elif record_sta == -1:
            log.error("Recording failed.")
            basic.d4.blink(100) # Blink Error LED fast

    def start_record(self, duration=10):
        if not self.record:
            log.error("Record object not initialized")
            return

        if self.is_recording:
            log.warning("Already recording")
            return

        try:
            try:
                uos.remove(self.record_file)
            except:
                pass

            log.info("Starting recording for {}s...".format(duration))
            # Start recording: filename, duration
            res = self.record.start(self.record_file, duration)
            if res == 0:
                self.is_recording = True
                basic.d3.on() # Turn on LED to indicate recording
            else:
                log.error("Failed to start recording, ret: {}".format(res))
        except Exception as e:
            log.error("Exception starting record: {}".format(e))

    def stop_record(self):
        if not self.record or not self.is_recording:
            return

        try:
            log.info("Stopping recording...")
            self.record.stop()
            self.is_recording = False
            basic.d3.off()
        except Exception as e:
            log.error("Exception stopping record: {}".format(e))

    def play_recording(self):
        if not self.aud:
            log.error("Audio playback object not initialized")
            return
            
        try:
            log.info("Playing back recording...")
            basic.d4.on() # Turn on Playback LED
            self.aud.play(1, 0, self.record_file)
            self.aud.setCallback(self._play_callback)
            
        except Exception as e:
            log.error("Exception playing record: {}".format(e))
            basic.d4.off()

    def _play_callback(self, event):
        # event: 0=Start, 7=Finish
        if event == 7:
            log.info("Playback finished.")
            basic.d4.off()

recorder = AudioRecorder()
