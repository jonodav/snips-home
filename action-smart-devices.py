#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from snipsTools import SnipsConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
from deviceCreds import *
import dataFromColor
import io
import socket
import random
import datetime as dt
import time

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
hi_tts = ["Welcome back", "Welcome home", 'Wonderful']
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

    def extract_brightness(self, intent_message):
        extractedBrightness = []
        if intent_message.slots.Brightness:
            for Brightness in intent_message.slots.Brightness.all():
                extractedBrightness.append(Brightness.value)
        return extractedBrightness

    def extract_devices(self, intent_message):
        extractedDevices = []
        if intent_message.slots.Device:
            for Device in intent_message.slots.Device.all():
                extractedDevices.append(Device.value)
        return extractedDevices

    def extract_colors(self, intent_message):
        extractedColors = []
        if intent_message.slots.Color:
            for Color in intent_message.slots.Color.all():
                extractedColors.append(Color.value)
        return extractedColors

    def extract_states(self, intent_message):
        extractedStates = []
        if intent_message.slots.State:
            for State in intent_message.slots.State.all():
                extractedStates.append(State.value)
        return extractedStates
    def extract_rooms(self, intent_message):
        extractedRooms = []
        if intent_message.slots.Room:
            for Room in intent_message.slots.Room.all():
                extractedRooms.append(Room.value)
        return extractedRooms
    def extract_sensorQueries(self, intent_message):
        extractedQueries = []
        if intent_message.slots.Data:
            for Data in intent_message.slots.Data.all():
                extractedQueries.append(Data.value)
        return extractedQueries
    
    def lightsOff(self):
        #Set downlights
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto("0", (downlightIP, downlightPort))
        #Set desk led strip
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto("f,0,0,0,0,0", (deskStripIP, deskStripPort))
        #Set smart lamp
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto("f,0,0,0", (smartlampIP, smartlampPort))
        #Set bedside lamp
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto("f,0", (bedsideLampIP, bedsideLampPort))

    def lightsOn(self):
        if dt.datetime.now().hour < 17:
            dlData = "f,818,1023"
            deskData = "f,0,0,0,0,255"
            rlData = "f,0"
        elif  dt.datetime.now().hour >= 17 and dt.datetime.now().hour < 18:
            dlData = "f,818,767"
            deskData = "f,0,0,0,255,255"
            rlData = "f,0"
        elif dt.datetime.now().hour >= 18 and dt.datetime.now().hour < 20:
            dlData = "f,818,512"
            deskData = "f,0,0,0,255,255"
            rlData = "f,0"
        elif dt.datetime.now().hour >= 20 and dt.datetime.now().hour < 22:
            dlData = "f,767,256"
            deskData = "f,0,0,0,255,0"
            rlData = "f," + str((dt.datetime.now().hour - 20) * 32)
        else: 
            dlData = "f,512,0"
            deskData = "f,0,0,0,255,0"
            rlData = "f,64"

        #Set downlights
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(dlData, (downlightIP, downlightPort))
        #Set desk led strip
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(deskData, (deskStripIP, deskStripPort))
        #Set bedside lamp
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto(rlData, (bedsideLampIP, bedsideLampPort))
        
    # --> Sub callback function, one per intent
    def onOffCallback(self, hermes, intent_message):
        # terminate the session first if not continue
        #hermes.publish_end_session(intent_message.session_id, "")
        
        # action code goes here...
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)

        ip = None

        self.Devices = self.extract_devices(intent_message)
        self.States = self.extract_states(intent_message)

        for x in range(0, len(self.Devices)):

            if len(self.States) != len(self.Devices):
                self.State = self.States[0]
            else:
                self.State = self.States[x]

            if self.Devices[x] == "downlights":
                ip = downlightIP
                port = downlightPort
                if self.State == "On":
                    data = "1"
                if self.State == "Off":
                    data = "0"
            if self.Devices[x] == "plug":
                ip = plugIP
                port = plugPort
                if self.State == "On":
                    data = "1"
                if self.State == "Off":
                    data = "0"
            if self.Devices[x] == "front room lamp":
                ip = frontLampIP
                port = frontLampPort
                if self.State == "On":
                    data = "1"
                if self.State == "Off":
                    data = "0"
            if self.Devices[x] == "living room lamp":
                ip = livingLampPort
                port = livingLampPort
                if self.State == "On":
                    data = "1"
                if self.State == "Off":
                    data = "0"
            if self.Devices[x] == "desk light":
                ip = deskStripIP
                port = deskStripPort
                if self.State == "Off":
                    data = "f,0,0,0,0,0"
                if self.State == "On":
                    data = "f,0,0,0,0,255"
            if self.Devices[x] == "bedside lamp":
                ip = bedsideLampIP
                port = bedsideLampPort
                if self.State == "Off":
                    data = "f,0"
                if self.State == "On":
                    data = "f,255"
            if self.Devices[x] == "smart lamp":
                ip = smartlampIP
                port = smartlampPort
                if self.State == "Off":
                    data = "f,0,0,0"
                if self.State == "On":
                    data = "f,255,255,255"

            if ip is not None:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
                sock.sendto(data, (ip, port))
                tts = random.choice(success_tts)
            else:
                tts = random.choice(fail_tts)

            if self.Devices[x] == "lights":
                tts = random.choice(success_tts)
                if self.State == "Off":
                    self.lightsOff()
                if self.State == "On":
                    self.lightsOn()
        #tts = "Turned the " + self.Device + " " + self.State

        # if need to speak the execution result by tts
        hermes.publish_end_session(intent_message.session_id, tts)

    def setBrightnessCallback(self, hermes, intent_message):
        # terminate the session first if not continue
        #hermes.publish_end_session(intent_message.session_id, "")

        # action code goes here...
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)

        self.Devices = self.extract_devices(intent_message)
        self.Brightnesses = self.extract_brightness(intent_message)

        for x in range(0, len(self.Devices)):

            if len(self.Brightnesses) != len(self.Devices):
                self.Brightness = self.Brightnesses[0]
            else:
                self.Brightness = self.Brightnesses[x]

            if self.Devices[x] == "downlights":
                ip = downlightIP
                port = downlightPort
                value = (float(self.Brightness) / 100) * 1023
                data = "l," + str(value)
            
            if self.Devices[x] == "bedside lamp":
                ip = bedsideLampIP
                port = bedsideLampPort
                value = (float(self.Brightness) / 100) * 255
                data = "f," + str(value)

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            sock.sendto(data, (ip, port))

        if self.Brightness is not None:
            tts = random.choice(success_tts)
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

        self.Devices = self.extract_devices(intent_message)
        self.Colors = self.extract_colors(intent_message)

        failed = False
        data = " "
        for x in range(0, len(self.Devices)):

            if len(self.Colors) != len(self.Devices):
                self.Color = self.Colors[0]
            else:
                self.Color = self.Colors[x]

            if self.Devices[x] == "downlights":
                ip = downlightIP
                port = downlightPort
                data = "t," + dataFromColor.ctFromColor(self.Color)
                deviceSet = True
            
            if self.Devices[x] == "desk light":
                ip = deskStripIP
                port = deskStripPort
                data = "f," + dataFromColor.rgbctFromColor(self.Color)
                deviceSet = True
            
            if self.Devices[x] == "smart lamp":
                ip = smartlampIP
                port = smartlampPort
                deviceSet = True
                if self.Color == "fire":
                    data = "b"
                elif self.Color == "clouds":
                    data = "d"
                elif self.Color == "cycle":
                    data = "c"
                elif self.Color == "rainbow":
                    data = "r"
                else: 
                    data = "f," + dataFromColor.rgbFromColor(self.Color)

            if data is not "fail":
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
                sock.sendto(data, (ip, port))
                if failed is False:
                    tts = random.choice(success_tts)
            else:
                failed = True
                tts = random.choice(fail_tts)

        
        hermes.publish_end_session(intent_message.session_id, tts)

    def fixDownlightCallback(self, hermes, intent_message):
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)

        hermes.publish_end_session(intent_message.session_id, "On it")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto("2", (downlightIP, downlightPort))
        time.sleep(1)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.sendto("2", (downlightIP, downlightPort))

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
            ip = downlightIP
            port = downlightPort
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
            sock.sendto(downlightData, (downlightIP, downlightPort))
            #Set desk led strip
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            sock.sendto(deskstripData, (deskStripIP, deskStripPort))
            #Set smart lamp
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            sock.sendto(smartlampData, (smartlampIP, smartlampPort))
            #Set bedside lamp
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            sock.sendto(bedlampData, (bedsideLampIP, bedsideLampPort))
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
        self.Word = "null"

        for (slot_value, slot) in intent_message.slots.items():
            if slot_value == "Animal":
                self.Animal = slot.first().value.encode("utf8")
            if slot_value == "Word":
                self.Word = slot.first().value.encode("utf8")

        self.lightsOff()

        if self.Animal == "aligator":
            tts = "In a while, crocodile!"
        elif self.Word == "night":
            tts = "Good night"
        else:
            tts = random.choice(bye_tts)
        hermes.publish_end_session(intent_message.session_id, tts)

    def returnCallback(self, hermes, intent_message):
        # terminate the session first if not continue
        #hermes.publish_end_session(intent_message.session_id, "")
        
        # action code goes here...
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)

        self.Word = "null"

        for (slot_value, slot) in intent_message.slots.items():
            if slot_value == "Word":
                self.Word = slot.first().value.encode("utf8")

        self.lightsOn()

        if self.Word == "morning":
            tts = "Good morning"
        elif self.Word == 'back':
            tts = "Welcome back"
        elif self.Word == 'home':
            tts = "Welcome home"
        else:
            tts = random.choice(hi_tts)
        hermes.publish_end_session(intent_message.session_id, tts)

    def getSensorDataCallback(self, hermes, intent_message):
        # terminate the session first if not continue
        #hermes.publish_end_session(intent_message.session_id, "")
        
        # action code goes here...
        print '[Received] intent: {}'.format(intent_message.intent.intent_name)

        self.Datas = ""
        
        self.Rooms = self.extract_rooms(intent_message)
        self.Datas = self.extract_sensorQueries(intent_message)

        tts = ""

        for x in range(0, len(self.Rooms)):
            if self.Rooms[x] == 'living room':
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
                sock.sendto("s", (livingtempIP, livingtempPort))
                sensorData = None
                start_time = time.time()
                while True:
                    if sock.recv != None:
                        sensorData, addr = sock.recvfrom(livingtempPort)
                        break
                    if (time.time() - start_time) > 2:
                        print("UDP Timeout")
                        break
                if x > 0:
                        tts += " and "
                if sensorData is not None:
                    tempHum = sensorData.split(",")
                    if self.Datas[x] == 'temperature':
                        tts += "The {0} temperature is {1} degrees".format(self.Rooms[x], tempHum[0])
                    elif self.Datas[x] == 'humidity':
                        tts += "The {0} humidity is {1} percent".format(self.Rooms[x], tempHum[1])
                    else:
                        tts += "The {0} temperature is {1} degrees with {2} percent humidity".format(self.Rooms[x], tempHum[0], tempHum[1])
                else: 
                    tts += "I couldnt reach the {0} sensor".format(self.Rooms[x])
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
                sock.sendto("s", (bedtempIP, bedtempPort))
                sensorData = None
                start_time = time.time()
                while True:
                    if sock.recv != None:
                        sensorData, addr = sock.recvfrom(bedtempPort)
                        break
                    if (time.time() - start_time) > 2:
                        print("UDP Timeout")
                        break
                if x > 0:
                        tts += " and "
                if sensorData is not None:
                    tempHum = sensorData.split(",")
                    if self.Datas[x] == 'temperature':
                        tts += "The {0} temperature is {1} degrees".format(self.Rooms[x], tempHum[0])
                    elif self.Datas[x] == 'humidity':
                        tts += "The {0} humidity is {1} percent".format(self.Rooms[x], tempHum[1])
                    else:
                        tts += "The {0} temperature is {1} degrees with {2} percent humidity".format(self.Rooms[x], tempHum[0], tempHum[1])
                else: 
                    tts += "I couldnt reach the {0} sensor".format(self.Rooms[x])

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
        if coming_intent == 'thejonnyd:FixDownlights':
            self.fixDownlightCallback(hermes, intent_message)
        if coming_intent == 'thejonnyd:GetSensorData':
            self.getSensorDataCallback(hermes, intent_message)

        # more callback and if condition goes here...

    # --> Register callback function and start MQTT
    def start_blocking(self):
        with Hermes(MQTT_ADDR) as h:
            h.subscribe_intents(self.master_intent_callback).start()
 
if __name__ == "__main__":
    SmartDevices()
