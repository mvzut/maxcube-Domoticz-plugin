# First attempt to create eQ-33 MAX! plugin
#
# Author: mvzut
#
"""
<plugin key="eq3max" name="eQ-3 MAX!" author="mvzut" version="0.4.2">
    <description>
        <h2>eQ-3 MAX! Cube plugin</h2><br/>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Thermostats and radiator valves are represented as Domoticz thermostat devices, which can be controlled (also by scripts), programmed, etc.</li>
            <li>Temperature sensors reflect the actual temperature retrieved from wall mounted thermostats or radiator valves.
            Note that radiator valves only report temperature when they are moving!</li>
            <li>Valve position of radiator valves is reflected in percentage sensors</li>
            <li>Status of door and window contacts is reflected in contact sensors</li>
            <li>(Optional) Thermostat modes can be viewed and changed with selector switches</li>
        </ul>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Fill in the IP address of your eQ-3 MAX! Cube</li>
            <li>Fill in the port number of your Cube. The default is 62910, no need to change this in most cases</li>
            <li>Select if you want the plugin to create selector switches for the thermostat modes</li>
            <li>Choose a polling time. The default is 5 minutes, shorter periods can sometimes cause problems, the eQ-3 MAX! system doesn't seem to like too much traffic per hour</li>
            <li>Choose the debug mode, when debugging is on it will be more verbose in the log</li>
        </ul>
    </description>
    <params>
        <param field="Address" label="Cube address" width="150px" required="true" default="192.168.0.1"/>
        <param field="Port" label="Cube port" width="75px" required="true" default="62910"/>
        <param field="Mode1" label="Use thermostat modes" width="75px" required="true">
            <options>
                <option label="No" value="False" default="true"/>
                <option label="Yes" value="True"/>
            </options>
        </param>
        <param field="Mode2" label="Poll every" width="150px" required="true">
            <options>
                <option label="1 minute" value=60/>
                <option label="2 minutes" value=120/>
                <option label="5 minutes (default)" value=300 default="true"/>
                <option label="10 minutes" value=600/>
                <option label="30 minutes" value=1800/>
            </options>
        </param>
        <param field="Mode3" label="Debug mode" width="75px" required="true">
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
        else:
            Domoticz.Debug("Could not create device with type " + typename)
            return
        # Check if device with given DeviceID and Type is already present
        DeviceFound = False
        for Device in Devices:
            if Devices[Device].DeviceID == deviceid and Devices[Device].Type == devicetype: DeviceFound = True
        # If not found, create it
        if not DeviceFound:
            Domoticz.Log("Creating device " + name + " - " + typename)
            Domoticz.Device(Name=name + " - " + typename, Unit=len(Devices)+1, DeviceID=deviceid, Type=devicetype, Subtype=subtype, Switchtype=switchtype, Options=options, Image = image, Used=1).Create()
        
    def onStart(self):
        # Set debugging
        if Parameters["Mode3"]=="True": 
            Domoticz.Debugging(2)
            Domoticz.Debug("Debugging mode activated")

        # Set heartbeat
        self.skipbeats=int(Parameters["Mode2"])/30
        self.beats=self.skipbeats
        Domoticz.Heartbeat(30)

        # Read Cube for intialization of devices
        Domoticz.Debug("Reading e-Q3 MAX! devices from Cube...")
        cube = MaxCube(MaxCubeConnection(Parameters["Address"], int(Parameters["Port"])))

        # Check which rooms have a wall thermostat
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
                    if Parameters["Mode1"]=="True": self.CheckDevice(EQ3device.name, EQ3device.rf_address, "Mode")
            elif cube.is_wallthermostat(EQ3device):
                self.CheckDevice(EQ3device.name, EQ3device.rf_address, "Thermostat")
                self.CheckDevice(EQ3device.name, EQ3device.rf_address, "Temperature")
                if Parameters["Mode1"]=="True": self.CheckDevice(EQ3device.name, EQ3device.rf_address, "Mode")
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
        cube = MaxCube(MaxCubeConnection(Parameters["Address"], int(Parameters["Port"])))

        # Update devices in Domoticz
        for EQ3device in cube.devices:
            Domoticz.Debug("Checking device '" + EQ3device.name + "' in room " + str(EQ3device.room_id))
            if cube.is_thermostat(EQ3device):
                # Look up & update Domoticz devices for radiator valves
                for DomDevice in Devices:
                    # Valve position
                    if Devices[DomDevice].Type == 243 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                        if Devices[DomDevice].sValue != str(EQ3device.valve_position):
                            Domoticz.Log("Updating valve position for " + Devices[DomDevice].Name + ": " + str(EQ3device.valve_position) + "%")
                            Devices[DomDevice].Update(nValue=0, sValue=str(EQ3device.valve_position), BatteryLevel=(255-EQ3device.battery*255))
                # Look up & update additional devices if room has no wall thermostat
                if not self.RoomHasThermostat[EQ3device.room_id]:
                    for DomDevice in Devices:
                        # Thermostat
                        if Devices[DomDevice].Type == 242 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                            if Devices[DomDevice].sValue != str(EQ3device.target_temperature):
                                Domoticz.Log("Updating setpoint for " + Devices[DomDevice].Name + ": " + str(EQ3device.target_temperature) + " \u00b0C")
                                Devices[DomDevice].Update(nValue=0, sValue=str(EQ3device.target_temperature), BatteryLevel=(255-EQ3device.battery*255))
                        # Temperature
                        elif Devices[DomDevice].Type == 80 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                            if EQ3device.actual_temperature and Devices[DomDevice].sValue != str(EQ3device.actual_temperature):
                                Domoticz.Log("Updating temperature for " + Devices[DomDevice].Name + ": " + str(EQ3device.actual_temperature) + " \u00b0C")
                                Devices[DomDevice].Update(nValue=0, sValue=str(EQ3device.actual_temperature), BatteryLevel=(255-EQ3device.battery*255))
                        # Thermostat mode
                        elif Devices[DomDevice].Type == 244 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                            mode = str(EQ3device.mode * 10)
                            if Devices[DomDevice].sValue != mode:
                                Domoticz.Log("Updating mode for " + Devices[DomDevice].Name)
                                Devices[DomDevice].Update(nValue=0, sValue=mode, BatteryLevel=(255-EQ3device.battery*255))
            elif cube.is_wallthermostat(EQ3device):
                # Look up & update Domoticz devices for wall thermostats
                for DomDevice in Devices:
                    # Thermostat
                    if Devices[DomDevice].Type == 242 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                        if Devices[DomDevice].sValue != str(EQ3device.target_temperature):
                            Domoticz.Log("Updating setpoint for " + Devices[DomDevice].Name + ": " + str(EQ3device.target_temperature) + " \u00b0C")
                            Devices[DomDevice].Update(nValue=0, sValue=str(EQ3device.target_temperature), BatteryLevel=(255-EQ3device.battery*255))
                    # Temperature
                    elif Devices[DomDevice].Type == 80 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                        if Devices[DomDevice].sValue != str(EQ3device.actual_temperature):
                            Domoticz.Log("Updating temperature for " + Devices[DomDevice].Name + ": " + str(EQ3device.actual_temperature) + " \u00b0C")
                            Devices[DomDevice].Update(nValue=0, sValue=str(EQ3device.actual_temperature), BatteryLevel=(255-EQ3device.battery*255))
                    # Thermostat mode
                    elif Devices[DomDevice].Type == 244 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                        mode = str(EQ3device.mode * 10)
                        if Devices[DomDevice].sValue != mode:
                            Domoticz.Log("Updating mode for " + Devices[DomDevice].Name)
                            Devices[DomDevice].Update(nValue=0, sValue=mode, BatteryLevel=(255-EQ3device.battery*255))
            elif cube.is_windowshutter(EQ3device):
                # Look up & update Domoticz device for contact switches
                for DomDevice in Devices:
                    if Devices[DomDevice].Type == 244 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                        if EQ3device.is_open == True:
                            nvalue = 1
                            svalue = "On"
                        elif EQ3device.is_open == False:
                            nvalue = 0
                            svalue = "Off"
                        if Devices[DomDevice].sValue != svalue: 
                            Domoticz.Log("Updating status for " + Devices[DomDevice].Name + ": " + svalue)
                            Devices[DomDevice].Update(nValue=nvalue, sValue=svalue, BatteryLevel=(255-EQ3device.battery*255))

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

