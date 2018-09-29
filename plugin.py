# First attempt to create eQ-33 MAX! plugin
#
# Author: mvzut
#
"""
<plugin key="eq3max" name="eQ-3 MAX!" author="mvzut" version="0.3.0">
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
from maxcube.device import \
    MAX_DEVICE_MODE_AUTOMATIC, \
    MAX_DEVICE_MODE_MANUAL, \
    MAX_DEVICE_MODE_VACATION, \
    MAX_DEVICE_MODE_BOOST

class BasePlugin:
    enabled = False
    def __init__(self):
        return
        
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

        # Check which rooms have a wall mounterd thermostat
        Domoticz.Debug("Number of rooms found: " + str(len(cube.rooms)))
        self.RoomHasThermostat=[False] * (len(cube.rooms)+1)
        for EQ3device in cube.devices:
            if cube.is_wallthermostat(EQ3device):
                self.RoomHasThermostat[EQ3device.room_id] = True
                Domoticz.Debug("Room " + str(EQ3device.room_id) + " (" + cube.room_by_id(EQ3device.room_id).name + ") has a thermostat")

        for EQ3device in cube.devices:
           # Add devices if required
            deviceFound = False
            for Device in Devices:
                if Devices[Device].DeviceID == EQ3device.rf_address: deviceFound = True
            if not deviceFound:
                Domoticz.Log("Adding device(s) for " + EQ3device.name)
                if cube.is_thermostat(EQ3device):
                    # Create percentage device for valve position
                    Domoticz.Device(Name=EQ3device.name + " - Valve position" , Unit=len(Devices)+1, DeviceID=EQ3device.rf_address, Type=243, Subtype=6, Used=1).Create()
                    if not self.RoomHasThermostat[EQ3device.room_id]:
                        # Create thermostat device
                        Domoticz.Device(Name=EQ3device.name + " - Thermostat", Unit=len(Devices)+1, DeviceID=EQ3device.rf_address, Type=242, Subtype=1, Used=1).Create()
                        # Create mode switch if requested
                        if Parameters["Mode1"]=="True":
                            Options = {"LevelActions": "||", 
                                       "LevelNames": "Auto|Manual|Vacation",
                                       "LevelOffHidden": "false",
                                       "SelectorStyle": "1"}
                            Domoticz.Device(Name=EQ3device.name + " - Mode", Unit=len(Devices)+1, DeviceID=EQ3device.rf_address, Type=244, Subtype=62, Switchtype=18,  Options=Options, Used=1).Create()
                        # Create temperature device
                        Domoticz.Device(Name=EQ3device.name + " - Temperature", Unit=len(Devices)+1, DeviceID=EQ3device.rf_address, Type=80, Subtype=5, Used=1).Create()
                if cube.is_wallthermostat(EQ3device):
                    # Create thermostat device
                    Domoticz.Device(Name=EQ3device.name + " - Thermostat", Unit=len(Devices)+1, DeviceID=EQ3device.rf_address, Type=242, Subtype=1, Used=1).Create()
                    # Create mode switch if requested
                    if Parameters["Mode1"]=="True":
                        Options = {"LevelActions": "||", 
                                    "LevelNames": "Auto|Manual|Vacation",
                                    "LevelOffHidden": "false",
                                    "SelectorStyle": "1"}
                        Domoticz.Device(Name=EQ3device.name + " - Mode", Unit=len(Devices)+1, Type=244, Subtype=62, Switchtype=18,  Options=Options, Used=1).Create()
                    # Create temperature device
                    Domoticz.Device(Name=EQ3device.name + " - Temperature", Unit=len(Devices)+1, DeviceID=EQ3device.rf_address, Type=80, Subtype=5, Used=1).Create()
                if cube.is_windowshutter(EQ3device):
                    # Create contact device
                    Domoticz.Device(Name=EQ3device.name, Unit=len(Devices)+1, DeviceID=EQ3device.rf_address, Type=244, Subtype=73, Switchtype=2, Used=1).Create()

    def onCommand(self, Unit, Command, Level, Hue):
        if Devices[Unit].Type == 242:
            Domoticz.Debug("Setpoint changed for " + Devices[Unit].Name + ". New setpoint: " + str(Level))
            cube = MaxCube(MaxCubeConnection(Parameters["Address"], int(Parameters["Port"])))
            for EQ3device in cube.devices:
                if Devices[Unit].DeviceID == EQ3device.rf_address:
                    cube.set_target_temperature(EQ3device, Level)
                    Devices[Unit].Update(nValue=0, sValue=str(Level))
                    Devices[Unit].Refresh()
        if Devices[Unit].Type == 244:
            if Level == 00:
                mode = MAX_DEVICE_MODE_AUTOMATIC
                mode_text = "Auto"
            elif Level == 10:
                mode = MAX_DEVICE_MODE_MANUAL
                mode_text = "Manual"
            elif Level == 20:
                mode = MAX_DEVICE_MODE_VACATION
                mode_text = "Vacation"
            Domoticz.Debug("Mode changed for " + Devices[Unit].Name + ". New mode: " + mode_text)
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
                # Look up & update corresponding Domoticz percentage device
                for DomDevice in Devices:
                    if Devices[DomDevice].Type == 243 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                        if Devices[DomDevice].sValue != str(EQ3device.valve_position):
                            Domoticz.Log("Updating valve position for " + Devices[DomDevice].Name + ": " + str(EQ3device.valve_position) + "%")
                            Devices[DomDevice].Update(nValue=0, sValue=str(EQ3device.valve_position), BatteryLevel=(255-EQ3device.battery*255))
                if not self.RoomHasThermostat[EQ3device.room_id]:
                    # Look up & update corresponding Domoticz thermostat device
                    for DomDevice in Devices:
                        if Devices[DomDevice].Type == 242 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                            if Devices[DomDevice].sValue != str(EQ3device.target_temperature):
                                Domoticz.Log("Updating setpoint for " + Devices[DomDevice].Name + ": " + str(EQ3device.target_temperature) + " \u00b0C")
                                Devices[DomDevice].Update(nValue=0, sValue=str(EQ3device.target_temperature), BatteryLevel=(255-EQ3device.battery*255))
                        # Update thermostat mode if available
                        if Devices[DomDevice].Type == 244 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                            if EQ3device.mode == MAX_DEVICE_MODE_AUTOMATIC: mode = "00"
                            elif EQ3device.mode == MAX_DEVICE_MODE_MANUAL: mode = "10"
                            elif EQ3device.mode == MAX_DEVICE_MODE_VACATION: mode = "20"
                            Domoticz.Log("Updating mode for " + Devices[DomDevice].Name)
                            Devices[DomDevice].Update(nValue=0, sValue=mode, BatteryLevel=(255-EQ3device.battery*255))
                    # Look up & update corresponding Domoticz temperature device
                    for DomDevice in Devices:
                        if Devices[DomDevice].Type == 80 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                            if EQ3device.actual_temperature and Devices[DomDevice].sValue != str(EQ3device.actual_temperature):
                                Domoticz.Log("Updating temperature for " + Devices[DomDevice].Name + ": " + str(EQ3device.actual_temperature) + " \u00b0C")
                                Devices[DomDevice].Update(nValue=0, sValue=str(EQ3device.actual_temperature), BatteryLevel=(255-EQ3device.battery*255))
            elif cube.is_wallthermostat(EQ3device):
                # Look up & update corresponding Domoticz thermostat device
                for DomDevice in Devices:
                    if Devices[DomDevice].Type == 242 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                        if Devices[DomDevice].sValue != str(EQ3device.target_temperature):
                            Domoticz.Log("Updating setpoint for " + Devices[DomDevice].Name + ": " + str(EQ3device.target_temperature) + " \u00b0C")
                            Devices[DomDevice].Update(nValue=0, sValue=str(EQ3device.target_temperature), BatteryLevel=(255-EQ3device.battery*255))
                        # Update thermostat mode if available
                        if Devices[DomDevice].Type == 244 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                            if EQ3device.mode == MAX_DEVICE_MODE_AUTOMATIC: mode = "00"
                            elif EQ3device.mode == MAX_DEVICE_MODE_MANUAL: mode = "10"
                            elif EQ3device.mode == MAX_DEVICE_MODE_VACATION: mode = "20"
                            if Devices[DomDevice].sValue != mode:
                                Domoticz.Log("Updating mode for " + Devices[DomDevice].Name)
                                Devices[DomDevice].Update(nValue=0, sValue=mode, BatteryLevel=(255-EQ3device.battery*255))
                # Look up & update corresponding Domoticz temperature device
                for DomDevice in Devices:
                    if Devices[DomDevice].Type == 80 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                        if Devices[DomDevice].sValue != str(EQ3device.actual_temperature):
                            Domoticz.Log("Updating temperature for " + Devices[DomDevice].Name + ": " + str(EQ3device.actual_temperature) + " \u00b0C")
                            Devices[DomDevice].Update(nValue=0, sValue=str(EQ3device.actual_temperature), BatteryLevel=(255-EQ3device.battery*255))
            elif cube.is_windowshutter(EQ3device):
                # Look up & update corresponding Domoticz contact device
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

