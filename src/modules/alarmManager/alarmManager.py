#!/usr/bin/env python
import pika
import sys
import argparse
sys.path.append( "./../../python" )
from rabbitConnection import RabbitConnection, ServerRequester
from alarm import Alarm
from serverHttpRequest import ServerHttpRequest
from os.path import expanduser
from ConfigParser import SafeConfigParser
import json
import time
import logging
import setproctitle

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(filename='module.log',level=logging.DEBUG, format=LOG_FORMAT)
queue_nameAlarm = "player"
queue_namePlayer = "alarm"
class AlarmManager:
    spotifyPlayer = None
    def __init__(self, config):
        LOGGER.info("starting alarm module")
        LOGGER.info("Getting a token")
        self.serverHttpRequest = ServerHttpRequest(config.get("Server", "url"),
                                                   config.get("Server", "username"),
                                                   config.get("Server", "password"))
        LOGGER.info("ServerHttpRequest ready")
        self.server = ServerRequester("serverRequest.player")
        Alarm.serverRequester = self.serverHttpRequest
        self.rabbitConnectionAlarm = RabbitConnection("module.alarm", "module.alarm")
        self.rabbitConnectionPlayer = RabbitConnection("module.player", "module.player")
        Alarm.rabbitConnectionPlayer = self.rabbitConnectionPlayer
        try:
            self.setHandlers()
            self.rabbitConnectionAlarm.onConnected(self.init)
            self.rabbitConnectionAlarm.start()
            self.rabbitConnectionPlayer.start()
            while True:
                  time.sleep(0.2)
        except KeyboardInterrupt:
            print("stopping consuming")
            self.server.stop()
            self.rabbitConnectionAlarm.stop()
            self.rabbitConnectionPlayer.stop()
            print("see ya later!")
            sys.exit(0)
    
    def init(self):
        self.server.emit("alarms:get");
     
    def setHandlers(self):
        LOGGER.info("set handlers")
        self.rabbitConnectionAlarm.addHandler("alarms:update", Alarm.responseToObject)
        self.rabbitConnectionAlarm.addHandler("alarms:new", Alarm.responseToObject)

        
if __name__ == '__main__':
    setproctitle.setproctitle("hommyPi_alarmManager")
    parser = argparse.ArgumentParser(description='Client for the HAPI server')
    parser.add_argument('--conf', help='Path to the configuration file')           
    args = parser.parse_args()
    confPath = expanduser("~") + '/.hommyPi_conf'
    if args.conf is not None:
       confPath = args.conf
    print(confPath)
    config = SafeConfigParser()
    config.read(confPath)
    alarmManager = AlarmManager(config)