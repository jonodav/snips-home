#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from snipsTools import SnipsConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import dataFromColor
import io
import socket
import random
import datetime as dt

CONFIG_INI = "config.ini"

# If this skill is supposed to run on the satellite,
# please get this mqtt connection info from <config.ini>
# Hint: MQTT server is always running on the master device
MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

success_tts = ['Got it', 'Sure', 'Done', 'Ok']
fail_tts = ["Sorry, I can't do that", "Sorry, that doesn't work", "No"]
bye_tts = ["Goodbye", "See you later", "Thank goodness"]
hi_tts = ["Welcome back", "Welcome home"]
no_slot_tts = ["What do you mean?", "Don't waste my time", "I can't do anything with that", "Please stop bothering me"]

class SmartDevices(object):
    """Class used to wrap action code with mqtt connection
        
        Please change the name refering to your application
    """

    def __init__(self):
        # get the configuration if needed
        try:
            self.config = SnipsConfigParser.read_configuration_file(CONFIG_INI)
        except :
            self.config = None

        # start listening to MQTT
        self.start_blocking()
        
    # --> Sub callback function, one per intent
    def onOffCallback(self, hermes, intent_message):
        # terminate the session first if not continue
        #hermes.publish_end_session(intent_message.session_id, "")
        
        # action code goes here...
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)

        # get the slots from intent
        for (slot_value, slot) in intent_message.slots.items():
            if slot_value == "Device":
                self.Device = slot.first().value.encode("utf8")
            if slot_value == "State":
                self.State = slot.first().value.encode("utf8")

        data = None

        if self.Device == "downlights":
            ip = "192.168.0.160"
            port = 16000
            if self.State == "On":
                data = "1"
            if self.State == "Off":
                data = "0"
        if self.Device == "desk light":
            ip = "192.168.0.181"
            port = 4221
            if self.State == "Off":
                data = "f,0,0,0,0,0"
            if self.State == "On":
                data = "f,0,0,0,0,255"
        if self.Device == "bedside lamp":
            ip = "192.168.0.180"
            port = 4220
            if self.State == "Off":
                data = "f,0"
            if self.State == "On":
                data = "f,255"
        if self.Device == "smart lamp":
            ip = "192.168.0.182"
            port = 4222
            if self.State == "Off":
                data = "f,0,0,0"
            if self.State == "On":
                data = "f,255,255,255"

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(data, (ip, port))

        if data is not None:
            tts = random.choice(success_tts)
        else:
            tts = random.choice(fail_tts)
        #tts = "Turned the " + self.Device + " " + self.State

        # if need to speak the execution result by tts
        hermes.publish_end_session(intent_message.session_id, tts)

    def setBrightnessCallback(self, hermes, intent_message):
        # terminate the session first if not continue
        #hermes.publish_end_session(intent_message.session_id, "")

        # action code goes here...
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)

        brightnessSet = False

        for (slot_value, slot) in intent_message.slots.items():
            if slot_value == "Device":
                self.Device = slot.first().value.encode("utf8")
            if slot_value == "Brightness":
                self.Brightness = slot.first().value.encode("utf8")
                brightnessSet = True

        deviceSet = False

        if self.Device == "downlights":
            ip = "192.168.0.160"
            port = 16000
            value = (float(self.Brightness) / 100) * 1023
            data = "l," + str(value)
            deviceSet = True
        
        if self.Device == "bedside lamp":
            ip = "192.168.0.180"
            port = 4220
            value = (float(self.Brightness) / 100) * 255
            data = "f," + str(value)
            deviceSet = True

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(data, (ip, port))

        if deviceSet and brightnessSet:
            tts = random.choice(success_tts)
        elif self.Brightness is None:
            tts = random.choice(no_slot_tts)
        else:
            tts = random.choice(fail_tts)
        #tts = self.Device + " set to " + self.Brightness + " percent"

        # if need to speak the execution result by tts
        hermes.publish_end_session(intent_message.session_id, tts)
    
    def setColorCallback(self, hermes, intent_message):
        # terminate the session first if not continue
        #hermes.publish_end_session(intent_message.session_id, "")

        # action code goes here...
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)

        for (slot_value, slot) in intent_message.slots.items():
            if slot_value == "Device":
                self.Device = slot.first().value.encode("utf8")

            if slot_value == "Color":
                self.Color = slot.first().value.encode("utf8")

        deviceSet = False
        data = " "

        if self.Device == "downlights":
            ip = "192.168.0.160"
            port = 16000
            data = "t," + dataFromColor.ctFromColor(self.Color)
            deviceSet = True
        
        if self.Device == "desk light":
            ip = "192.168.0.181"
            port = 4221
            data = "f," + dataFromColor.rgbctFromColor(self.Color)
            deviceSet = True
        
        if self.Device == "smart lamp":
            ip = "192.168.0.182"
            port = 4222
            deviceSet = True
            if self.Color == "fire":
                data = "b"
            elif self.Color == "clouds":
                data = "d"
            elif self.Color == "cycle":
                data = "c"
            else: 
                data = "f," + dataFromColor.rgbFromColor(self.Color)

        if data is not "fail" and deviceSet:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            sock.sendto(data, (ip, port))
            tts = random.choice(success_tts)
        elif deviceSet == False:
            tts = random.choice(no_slot_tts)
        else:
            tts = random.choice(fail_tts)
        
        hermes.publish_end_session(intent_message.session_id, tts)

    def setBrightnessColorCallback(self, hermes, intent_message):
        # terminate the session first if not continue
        #hermes.publish_end_session(intent_message.session_id, "")

        # action code goes here...
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)
        brightnessSet = False

        for (slot_value, slot) in intent_message.slots.items():
            if slot_value == "Device":
                self.Device = slot.first().value.encode("utf8")

            if slot_value == "Color":
                self.Color = slot.first().value.encode("utf8")
            
            if slot_value == "Brightness":
                self.Brightness = slot.first().value.encode("utf8")
                brightnessSet = True

        deviceSet = False
        data = " "

        if self.Device == "downlights":
            ip = "192.168.0.160"
            port = 16000
            value = (float(self.Brightness) / 100) * 1023
            data = "f," + str(value) + "," + dataFromColor.ctFromColor(self.Color)
            deviceSet = True
        

        if brightnessSet and deviceSet:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            sock.sendto(data, (ip, port))
            tts = random.choice(success_tts)
        elif deviceSet == False:
            tts = random.choice(no_slot_tts)
        else:
            tts = random.choice(fail_tts)
        
        hermes.publish_end_session(intent_message.session_id, tts)

    def setSceneCallback(self, hermes, intent_message):
        # terminate the session first if not continue
        #hermes.publish_end_session(intent_message.session_id, "")

        # action code goes here...
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)

        for (slot_value, slot) in intent_message.slots.items():
            if slot_value == "Scene":
                self.Scene = slot.first().value.encode("utf8")
        
        sceneData = False

        if self.Scene == "day":
            downlightData = "f,1023,1023,1000"
            deskstripData = "f,0,0,0,0,255"
            smartlampData = "g,0,0,100,90,100,0"
            bedlampData = "f,0"
            sceneData = True
        elif self.Scene == "lights out":
            downlightData = "0"
            deskstripData = "f,0,0,0,0,0"
            smartlampData = "f,0,0,0"
            bedlampData = "f,0"
            sceneData = True
        elif self.Scene == "reading":
            downlightData = "0"
            deskstripData = "f,255,0,0,0,0"
            smartlampData = "f,16,0,0"
            bedlampData = "f,5"
            sceneData = True
        elif self.Scene == "blue":
            downlightData = "f,256,0,1000"
            deskstripData = "f,0,0,255,0,0"
            smartlampData = "f,0,0,255"
            bedlampData = "f,39"
            sceneData = True
        elif self.Scene == "dim":
            downlightData = "0"
            deskstripData = "f,255,0,0,0,0"
            smartlampData = "f,0,0,0"
            bedlampData = "f,1"
            sceneData = True
        elif self.Scene == "calm":
            downlightData = "f,756,1023,1000"
            deskstripData = "f,0,0,255,0,48"
            smartlampData = "d"
            bedlampData = "f,39"
            sceneData = True
        elif self.Scene == "cozy":
            downlightData = "f,50,0,1000"
            deskstripData = "f,0,0,0,255,0"
            smartlampData = "b"
            bedlampData = "f,39"
            sceneData = True

        if sceneData is True:
            #Set downlights
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            sock.sendto(downlightData, ("192.168.0.160", 16000))
            #Set desk led strip
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            sock.sendto(deskstripData, ("192.168.0.181", 4221))
            #Set smart lamp
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            sock.sendto(smartlampData, ("192.168.0.182", 4222))
            #Set bedside lamp
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            sock.sendto(bedlampData, ("192.168.0.180", 4220))
            tts = random.choice(success_tts)
        else:
            tts = random.choice(fail_tts)
            
        hermes.publish_end_session(intent_message.session_id, tts)

    def leavingCallback(self, hermes, intent_message):
        # terminate the session first if not continue
        #hermes.publish_end_session(intent_message.session_id, "")
        
        # action code goes here...
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)

        self.Animal = "null"

        for (slot_value, slot) in intent_message.slots.items():
            if slot_value == "Animal":
                self.Animal = slot.first().value.encode("utf8")

        #Set downlights
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto("0", ("192.168.0.160", 16000))
        #Set desk led strip
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto("f,0,0,0,0,0", ("192.168.0.181", 4221))
        #Set smart lamp
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto("f,0,0,0", ("192.168.0.182", 4222))
        #Set bedside lamp
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto("f,0", ("192.168.0.180", 4220))

        if self.Animal == "aligator":
            tts = "In a while, crocodile!"
        else:
            tts = random.choice(bye_tts)
        hermes.publish_end_session(intent_message.session_id, tts)

    def returnCallback(self, hermes, intent_message):
        # terminate the session first if not continue
        #hermes.publish_end_session(intent_message.session_id, "")
        
        # action code goes here...
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)

        if dt.datetime.now().hour < 15:
            dlData = "f,818,1023"
            deskData = "f,0,0,0,0,255"
            rlData = "f,0"
        elif dt.datetime.now().hour >= 15 and dt.datetime.now().hour < 19:
            dlData = "f,818,512"
            deskData = "f,0,0,0,255,255"
            lampBrightness = (dt.datetime.now().hour - 18) * 20
            if lampBrightness < 0:
                lampBrightness = 0
            rlData = "f," + str(lampBrightness)
        elif dt.datetime.now().hour >= 19 and dt.datetime.now().hour < 21:
            dlData = "f,767,256"
            deskData = "f,0,0,0,255,0"
            rlData = "f," + str((dt.datetime.now().hour - 18) * 20)
        else: 
            dlData = "f,512,0"
            deskData = "f,0,0,0,255,0"
            rlData = "f,128"

        #Set downlights
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(dlData, ("192.168.0.160", 16000))
        #Set desk led strip
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(deskData, ("192.168.0.181", 4221))
        #Set bedside lamp
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(rlData, ("192.168.0.180", 4220))

        tts = random.choice(hi_tts)
        hermes.publish_end_session(intent_message.session_id, tts)

    # --> Master callback function, triggered everytime an intent is recognized
    def master_intent_callback(self,hermes, intent_message):
        coming_intent = intent_message.intent.intent_name
        if coming_intent == 'thejonnyd:OnOff':
            self.onOffCallback(hermes, intent_message)
        if coming_intent == 'thejonnyd:SetBrightness':
            self.setBrightnessCallback(hermes, intent_message)
        if coming_intent == 'thejonnyd:SetColor':
            self.setColorCallback(hermes, intent_message)
        if coming_intent == 'thejonnyd:SetScene':
            self.setSceneCallback(hermes, intent_message)
        if coming_intent == 'thejonnyd:Leaving':
            self.leavingCallback(hermes, intent_message)
        if coming_intent == 'thejonnyd:Returning':
            self.returnCallback(hermes, intent_message)
        if coming_intent == 'thejonnyd:SetBrightnessAndColor':
            self.setBrightnessColorCallback(hermes, intent_message)

        # more callback and if condition goes here...

    # --> Register callback function and start MQTT
    def start_blocking(self):
        with Hermes(MQTT_ADDR) as h:
            h.subscribe_intents(self.master_intent_callback).start()
 
if __name__ == "__main__":
    SmartDevices()
