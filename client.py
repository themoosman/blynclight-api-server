#!/usr/bin/python3

import time
import logging
import sys
import traceback
import os
import configparser
import distutils
import requests
from os import path
from flask import json


##############################################################################
# Main functionality
##############################################################################
class BlynclightClient(object):
    """Class with main function of BlynclightStatus"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.appconfig = self.config['app']
        self.globalconfig = self.config['global']
        self.last_code = -1

    def sleep(self, wait_time):
        """Basic Sleep Function"""
        self.logger.info("Sleeping: " + str(wait_time) + " seconds")
        time.sleep(wait_time)

    def make_rest_call(self, api_server, service, j):
        self.logger.debug("api_server: " + api_server)
        self.logger.debug("service-name: " + service)
        self.logger.debug("json: " + json.dumps(j))
        try:
            resp = requests.post(api_server + service, data=json.dumps(j), headers={'Content-Type': 'application/json'})
        except ConnectionError as e:
            self.logger.error("Connection error: " + ".  Error: " + str(e))
            time.sleep(60)
            return
        except Exception:
            self.logger.error("Unknown connection error: %s", sys.exc_info()[0])
            time.sleep(60)
            return

        if resp.status_code != 200:
            self.logger.error("API call failed, response code is: " + str(resp.status_code) + ".  Error: " + resp.error)
        return resp.json

    def main(self):
        """Main functionality"""

        try:
            # Set up logging
            log_datefmt = '%m-%d-%Y,%H:%M:%S'
            log_fmt = '%(asctime)-15s %(levelname)-8s %(message)s'
            log_level = logging.getLevelName(self.appconfig.get(
                'log_level', self.globalconfig.get('log_level', 'INFO')))
            log_file = self.appconfig.get('client_log_file')
            # log_level = logging.INFO

            if "TTY" in os.environ:
                logging.basicConfig(format=log_fmt, datefmt=log_datefmt, level=log_level)
            else:
                if sys.stdout.isatty():
                    # Connected to a real terminal - log to stdout
                    logging.basicConfig(format=log_fmt, datefmt=log_datefmt, level=log_level)
                else:
                    # Background mode - log to file
                    logging.basicConfig(format=log_fmt, datefmt=log_datefmt, level=log_level, filename=log_file)

            # Banner
            self.logger.info("==========================================================")
            self.logger.info("")
            self.logger.info("Running BlynclightClient")
            self.logger.info("")
            self.logger.info("==========================================================")

            self.logger.info("starting control loop")
            while True:
                self.logger.debug("noop")
                case_value = 0

                # reload configs
                self.config.read('config.ini')
                self.appconfig = self.config['app']
                self.globalconfig = self.config['global']
                self.logger.setLevel(logging.getLevelName(self.appconfig.get(
                    'log_level', self.globalconfig.get('log_level', 'INFO'))))
                headset = self.appconfig['headset_status']
                headset_stream = self.appconfig['headset_stream']
                webcam = self.appconfig['webcam_device']
                wait_time = int(self.appconfig.get('wait_time', '10'))
                long_wait_time = int(self.appconfig.get('long_wait_time', '60'))
                no_headset_wait_time = int(self.appconfig.get('no_headset_wait_time', '60'))
                use_headset_ctrl = distutils.util.strtobool(self.appconfig.get('use_headset_ctrl', 'True'))
                api_server = self.appconfig.get('api_server', 'http://localhost:8080/api/v1/')
                skip = False

                # check headset on/off
                if use_headset_ctrl:
                    self.logger.info("Looking for headset")
                    # stream = os.popen('headsetcontrol -b | grep -i battery | wc -l')
                    # stream = os.popen('cat ' + headset + ' | grep -i "closed" | wc -l')
                    if not path.isfile(headset_stream):
                        self.logger.info("Headset stream file not found")
                        # headset off or not found
                        self.logger.debug("break 0.1")
                        self.logger.info("Headset not found")
                    else:
                        self.logger.info("Headset stream file found")
                        stream = os.popen('cat ' + headset + ' | grep -i "closed" | wc -l')
                        self.logger.debug("0.0: ")
                        output = stream.read().strip()
                        self.logger.debug("0:lc " + output)
                        line_count = int(output)
                        if line_count < 2:
                            # headset found
                            self.logger.debug("break 0.0")
                            self.logger.info("Headset found without active status")
                            case_value += 1
                        else:
                            self.logger.info("Headset status showed as closed")
                else:
                    skip = True

                self.logger.debug("case_value: " + str(case_value))

                # check headset activity only if it was found above or check is skipped.
                if case_value > 0 or skip:
                    self.logger.info("Checking for headset activity")
                    stream = os.popen('cat ' + headset + ' | grep -i "RUNNING" | wc -l')
                    output = stream.read().strip()
                    # self.logger.debug("1: " + output)
                    line_count = int(output)
                    if line_count == 0:
                        self.logger.debug("break 1.0")
                        self.logger.info("Headset found but not active")
                        case_value += 1
                    else:
                        self.logger.debug("break 1.1")
                        self.logger.info("Headset is active")
                        case_value += 1
                        case_value += 1
                    if skip:
                        case_value += 1
                    self.logger.debug("case_value: " + str(case_value))

                if case_value > 2:
                    # check for active webcam
                    self.logger.info("Looking for webcam")
                    # light.color = red
                    stream = os.popen('lsof -t ' + webcam + ' |  wc -l')
                    output = stream.read().strip()
                    self.logger.debug("2: " + output)
                    line_count = int(output)
                    if line_count > 0:
                        self.logger.debug("break 2")
                        self.logger.info("Webcam is active")
                        case_value += 1
                    else:
                        self.logger.debug("break 2")
                        self.logger.info("Webcam not active")
                    self.logger.debug("case_value: " + str(case_value))

                if case_value == 0:
                    self.logger.debug("hit case 0")
                    self.make_rest_call(api_server, 'color_name', {'color_name': 'green'})
                    self.make_rest_call(api_server, 'flash', {'flash': False})
                    self.make_rest_call(api_server, 'on', {'on': True})
                    self.sleep(no_headset_wait_time)
                    continue
                if case_value == 1:
                    # headset found but not running
                    self.logger.debug("hit case 1")
                    self.make_rest_call(api_server, 'color_name', {'color_name': 'green'})
                    self.make_rest_call(api_server, 'flash', {'flash': False})
                    self.make_rest_call(api_server, 'on', {'on': True})
                    self.sleep(wait_time)
                    continue
                elif case_value == 2:
                    # headset found and active, but not output
                    self.logger.debug("hit case 2")
                    self.make_rest_call(api_server, 'color_name', {'color_name': 'yellow'})
                    self.make_rest_call(api_server, 'flash', {'flash': False})
                    self.sleep(1)
                    self.make_rest_call(api_server, 'on', {'on': True})
                    self.sleep(wait_time)
                    continue
                elif case_value == 3:
                    # headset found and active, with output
                    self.logger.debug("hit case 3")
                    self.make_rest_call(api_server, 'color_name', {'color_name': 'red'})
                    self.make_rest_call(api_server, 'flash', {'flash': False})
                    self.make_rest_call(api_server, 'on', {'on': True})
                    self.sleep(wait_time)
                    continue
                elif case_value == 4:
                    # headset found and active, with output and active webcam
                    self.logger.debug("hit case 4")
                    self.make_rest_call(api_server, 'color_name', {'color_name': 'red'})
                    self.make_rest_call(api_server, 'flash', {'flash': True})
                    self.make_rest_call(api_server, 'speed', {'speed': 4})
                    self.make_rest_call(api_server, 'on', {'on': True})
                    self.sleep(wait_time)
                    continue
                elif case_value == 5:
                    self.logger.debug("hit case 5")
                    self.make_rest_call(api_server, 'color_name', {'color_name': 'magenta'})
                    self.make_rest_call(api_server, 'flash', {'flash': True})
                    self.make_rest_call(api_server, 'speed', {'speed': 4})
                    self.make_rest_call(api_server, 'on', {'on': True})
                    self.logger.info("how the fuck did you get here?")
                    time.sleep(long_wait_time)
                    continue

                time.sleep(long_wait_time)

        except KeyboardInterrupt:
            try:
                self.make_rest_call(api_server, 'color_name', {'color_name': 'blank'})
                self.make_rest_call(api_server, 'on', {'on': False})
            except Exception:
                logging.critical("Unable to reset light")
            logging.critical("Terminating due to keyboard interrupt")
        except Exception:
            try:
                self.make_rest_call(api_server, 'color_name', {'color_name': 'blank'})
                self.make_rest_call(api_server, 'on', {'on': False})
            except Exception:
                logging.critical("Unable to reset light")
            logging.critical("Terminating due to unexpected error: %s", sys.exc_info()[0])
            logging.critical("%s", traceback.format_exc())


if __name__ == "__main__":
    BlynclightClient().main()
