# First attempt to create eQ-33 MAX! plugin
#
# Author: mvzut
#
"""
<plugin key="eq3max" name="eQ-3 MAX!" author="mvzut" version="0.5.2">
    <description>
        <h2>eQ-3 MAX! Cube plugin</h2><br/>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Automatically creates devices for all your wall mounted thermostats, radiator valves and door/window sensors.</li>
            <li>If a room has a wall thermostat, this will act as setpoint and temperature sensor in that room.
            Otherwise, thermostats and temperature sensors will be created for every radiator valve.
            Note that radiator valves only report temperature when the valves are moving!</li>
            <li>Thermostats and door/window switches are always created. Temperature sensors, valve positions and thermostat mode switches are optional.</li>
        </ul>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Fill in the IP address of your eQ-3 MAX! Cube</li>
            <li>Fill in the port number of your Cube. The default is 62910, ther is no need to change this in most cases.</li>
            <li>Select which  device types you want the plugin to create.</li>
            <li>Choose a polling time. The default is 5 minutes, shorter periods can sometimes cause problems, the eQ-3 MAX! system doesn't seem to like too much traffic per hour.</li>
            <li>Select if obsolete devices should be deleted (i.e. if you later decide you don't want specific device types).</li>
            <li>Choose the debug mode, when debugging is on it will be more verbose in the log.</li>
        </ul>
    </description>
    <params>
        <param field="Address" label="Cube address" width="150px" required="true" default="192.168.0.1"/>
        <param field="Port" label="Cube port" width="150px" required="true" default="62910"/>
        <param field="Mode1" label="Temperature sensors" width="150px" required="true">
            <options>
                <option label="Do not create" value="False"/>
                <option label="Create &amp; update" value="True" default="true"/>
            </options>
        </param>
        <param field="Mode2" label="Valve positions" width="150px" required="true">
            <options>
                <option label="Do not create" value="False"/>
                <option label="Create &amp; update" value="True" default="true"/>
            </options>
        </param>
        <param field="Mode3" label="Thermostat modes" width="150px" required="true">
            <options>
                <option label="Do not create" value="False" default="true"/>
                <option label="Create &amp; update" value="True"/>
            </options>
        </param>
        <param field="Mode4" label="Update every" width="150px" required="true">
            <options>
                <option label="1 minute" value=60/>
                <option label="2 minutes" value=120/>
                <option label="5 minutes (default)" value=300 default="true"/>
                <option label="10 minutes" value=600/>
                <option label="30 minutes" value=1800/>
            </options>
        </param>
        <param field="Mode5" label="Remove obsolete devices" width="75px" required="true">
            <options>
                <option label="Yes" value="True" default="true"/>
                <option label="No" value="False"/>
            </options>
        </param>
        <param field="Mode6" label="Debug mode" width="75px" required="true">
            <options>
                <option label="Off" value="False" default="true"/>
                <option label="On" value="True"/>
            </options>
        </param>
    </params>
</plugin>
"""


import Domoticz
from maxcube.cube import MaxCube
from maxcube.connection import MaxCubeConnection

class BasePlugin:
    enabled = False
    def __init__(self):
        return


    def CheckDevice(self, name, deviceid, typename):
        # Initialization of variables for device creation
        switchtype = 0
        image = 0
        options = {"LevelActions": "|||", 
                   "LevelNames": "Auto|Manual|Vacation|Boost",
                   "LevelOffHidden": "false",
                   "SelectorStyle": "0"}        
        if typename == "Valve":
            devicetype = 243
            subtype = 6
        elif typename == "Thermostat":
            devicetype = 242
            subtype = 1
        elif typename == "Temperature":
            devicetype = 80
            subtype = 5
        elif typename == "Mode":
            devicetype = 244
            subtype = 62
            switchtype = 18
            image = 15
        elif typename == "Contact":
            devicetype = 244
            subtype = 73
            switchtype = 2

        # Check if device is wanted
        DeviceWanted = True
        if Parameters["Mode2"] == "False" and typename == "Valve" or \
           Parameters["Mode1"] == "False" and typename == "Temperature" or \
           Parameters["Mode3"] == "False" and typename == "Mode":
            DeviceWanted = False

        # Check if device with given deviceid and devicetype is already present
        DeviceFound = False
        for Device in Devices:
            if Devices[Device].DeviceID == deviceid and Devices[Device].Type == devicetype:
                DeviceFound = True
                # Delete found device if not wanted anymore and "Delete obsolete devices" is turned on
                if not DeviceWanted and Parameters["Mode5"] == "True":
                    Domoticz.Log("Deleting device " + Devices[Device].Name)
                    Devices[Device].Delete()
                    break

        # If device not found but wanted, create it
        if not DeviceFound and DeviceWanted:
            old_device_count = len(Devices)
            Domoticz.Device(Name=name + " - " + typename, Unit=len(Devices)+1, DeviceID=deviceid, Type=devicetype, Subtype=subtype, Switchtype=switchtype, Options=options, Image = image, Used=1).Create()
            if len(Devices) != old_device_count:
                # Device created
                Domoticz.Log("Created device '" + Parameters["Name"] + " - " + name + " - " + typename + "'")
            else:
                # Device not created!
                Domoticz.Error("Device '" + Parameters["Name"] + " - " + name + " - " + typename + "' could not be created. Is 'Accept new Hardware Devices' enabled under Settings?")


    def UpdateDevice(self, DOMdevice, EQ3device, typename):
        nvalue = 0
        if typename == "Valve":
            devicetype = 243
            svalue = str(EQ3device.valve_position)
        elif typename == "Thermostat":
            devicetype = 242
            svalue = str(EQ3device.target_temperature)
        elif typename == "Temperature":
            devicetype = 80
            svalue = str(EQ3device.actual_temperature)
        elif typename == "Mode":
            devicetype = 244
            svalue = str(EQ3device.mode * 10)    
        elif typename == "Contact":
            devicetype = 244
            if EQ3device.is_open == False:
                svalue = "Off"
            elif EQ3device.is_open == True:
                svalue = "On"
                nvalue = 1

        # Update device if it matches and if it has changed
        if Devices[DOMdevice].Type == devicetype and Devices[DOMdevice].DeviceID == EQ3device.rf_address:
            if Devices[DOMdevice].sValue != svalue and svalue !=0:
                Domoticz.Log("Updating " + Devices[DOMdevice].Name)
                Devices[DOMdevice].Update(nValue=nvalue, sValue=svalue, BatteryLevel=(255-EQ3device.battery*255))


    def onStart(self):
        # Set heartbeat
        self.skipbeats=int(Parameters["Mode4"])/30
        self.beats=self.skipbeats
        Domoticz.Heartbeat(30)

        # Set debugging
        if Parameters["Mode6"]=="True": 
            Domoticz.Debugging(2)
            Domoticz.Debug("Debugging mode activated")

        # Read Cube for intialization of devices
        Domoticz.Debug("Reading e-Q3 MAX! devices from Cube...")
        try:
            cube = MaxCube(MaxCubeConnection(Parameters["Address"], int(Parameters["Port"])))
        except:
            Domoticz.Error("Error connecting to Cube")
            return
        
        # Check which rooms have a wall mounterd thermostat
        max_room = 0
        for room in cube.rooms:
            if room.id > max_room: max_room = room.id
        Domoticz.Debug("Number of rooms found: " + str((len(cube.rooms))) + " (highest number: " + str(max_room) + ")")
        self.RoomHasThermostat=[False] * (max_room+1)
        for EQ3device in cube.devices:
            if cube.is_wallthermostat(EQ3device):
                self.RoomHasThermostat[EQ3device.room_id] = True
                Domoticz.Debug("Room " + str(EQ3device.room_id) + " (" + cube.room_by_id(EQ3device.room_id).name + ") has a thermostat")

        # Create devices if necessary
        for EQ3device in cube.devices:
            if cube.is_thermostat(EQ3device):
                self.CheckDevice(EQ3device.name, EQ3device.rf_address, "Valve")
                if not self.RoomHasThermostat[EQ3device.room_id]:
                    self.CheckDevice(EQ3device.name, EQ3device.rf_address, "Thermostat")
                    self.CheckDevice(EQ3device.name, EQ3device.rf_address, "Temperature")
                    self.CheckDevice(EQ3device.name, EQ3device.rf_address, "Mode")
            elif cube.is_wallthermostat(EQ3device):
                self.CheckDevice(EQ3device.name, EQ3device.rf_address, "Thermostat")
                self.CheckDevice(EQ3device.name, EQ3device.rf_address, "Temperature")
                self.CheckDevice(EQ3device.name, EQ3device.rf_address, "Mode")
            elif cube.is_windowshutter(EQ3device):
                self.CheckDevice(EQ3device.name, EQ3device.rf_address, "Contact")
 
    def onCommand(self, Unit, Command, Level, Hue):
        if Devices[Unit].Type == 242:
            Domoticz.Debug("Setpoint changed for " + Devices[Unit].Name + ". New setpoint: " + str(Level))
            cube = MaxCube(MaxCubeConnection(Parameters["Address"], int(Parameters["Port"])))
            for EQ3device in cube.devices:
                if Devices[Unit].DeviceID == EQ3device.rf_address:
                    cube.set_target_temperature(EQ3device, Level)
                    Devices[Unit].Update(nValue=0, sValue=str(Level))
                    Devices[Unit].Refresh()

        if Devices[Unit].Type == 244 and Devices[Unit].SubType == 62:
            if Level == 00:
                mode = 0
                mode_text = "Auto"
            elif Level == 10:
                mode = 1
                mode_text = "Manual"
            elif Level == 20:
                mode = 2
                mode_text = "Vacation"
            elif Level == 30:
                mode = 3
                mode_text = "Boost"
            Domoticz.Log("Mode changed for " + Devices[Unit].Name + ". New mode: " + mode_text)
            cube = MaxCube(MaxCubeConnection(Parameters["Address"], int(Parameters["Port"])))
            for EQ3device in cube.devices:
                if Devices[Unit].DeviceID == EQ3device.rf_address:
                    cube.set_mode(EQ3device, mode)
                    Devices[Unit].Update(nValue=0, sValue=str(Level))
                    Devices[Unit].Refresh()


    def onHeartbeat(self):
        #Cancel the rest of this function if this heartbeat needs to be skipped
        if self.beats < self.skipbeats:
            Domoticz.Debug("Skipping heartbeat: " + str(self.beats))
            self.beats += 1
            return
        self.beats=1

        # Read data from Cube
        Domoticz.Debug("Reading e-Q3 MAX! devices from Cube...")
        try:
            cube = MaxCube(MaxCubeConnection(Parameters["Address"], int(Parameters["Port"])))
        except:
            Domoticz.Error("Error connecting to Cube")
            return

        # Update devices in Domoticz
        for EQ3device in cube.devices:
            Domoticz.Debug("Checking device '" + EQ3device.name + "' in room " + str(EQ3device.room_id))
            if cube.is_thermostat(EQ3device):
                # Look up & update Domoticz devices for radiator valves
                for DomDevice in Devices:
                    self.UpdateDevice(DomDevice, EQ3device, "Valve")
                if not self.RoomHasThermostat[EQ3device.room_id]:
                    for DomDevice in Devices:
                        self.UpdateDevice(DomDevice, EQ3device, "Thermostat")
                        self.UpdateDevice(DomDevice, EQ3device, "Temperature")
                        self.UpdateDevice(DomDevice, EQ3device, "Mode")

            elif cube.is_wallthermostat(EQ3device):
                # Look up & update Domoticz devices for wall thermostats
                for DomDevice in Devices:
                    self.UpdateDevice(DomDevice, EQ3device, "Thermostat")
                    self.UpdateDevice(DomDevice, EQ3device, "Temperature")
                    self.UpdateDevice(DomDevice, EQ3device, "Mode")

            elif cube.is_windowshutter(EQ3device):
                # Look up & update Domoticz device for contact switches
                for DomDevice in Devices:
                    self.UpdateDevice(DomDevice, EQ3device, "Contact")


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

