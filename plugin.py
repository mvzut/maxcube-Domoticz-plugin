# First attempt to create eQ-33 MAX! plugin
#
# Author: mvzut
#
"""
<plugin key="eq3max" name="eQ-3 MAX!" author="mvzut" version="0.1.0">
    <description>
        <h2>eQ-3 MAX! Cube plugin</h2><br/>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Thermostats and radiator valves are represented as Domoticz thermostat devices, which can be controlled (also by scripts), programmed, etc.</li>
            <li>Temperature sensors reflect the actual temperature retrieved from wall mounted thermostats or (when 'Use radiator valves' is selected as thermostat mode) from radiator valves.
            Note that radiator valves only report temperature when they are moving!</li>
            <li>Valve position of radiator valves is reflected in percentage sensors</li>
            <li>Status of door and window contacts is reflected in contact sensors</li>
        </ul>
        <h3>Not working yet</h3>
        <ul style="list-style-type:square">
            <li>Adding devices (this has to be done using the eQ-3 MAX! software)</li>
            <li>Auto/Manual/Holiday modes. In principle you don't need them anymore, since you can program your own timers and scripts for thermostats</li>
        </ul>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Fill in the IP address of your eQ-3 MAX! Cube</li>
            <li>Fill in the port number of your Cube. The default is 62910, no need to change this in most cases.</li>
            <li>Select if you want Domoticz thermostats to be created based on your radiator valves or your wall mounted thermostats (if you have those).</li>
            <li>Choose a polling time. The default is 5 minutes, shorter periods can sometimes cause problems, the eQ-3 MAX! system doesn't seem to like too much traffic per hour.</li>
        </ul>
    </description>
    <params>
        <param field="Address" label="Cube address" width="150px" required="true" default="192.168.0.1"/>
        <param field="Port" label="Cube port" width="75px" required="true" default="62910"/>
        <param field="Mode1" label="Thermostat mode" width="300px" required="true">
            <options>
                <option label="Use radiator valves" value="RV" default="true"/>
                <option label="Use wall mounted thermostats if available" value="WMT"/>
            </options>
        </param>
        <param field="Mode2" label="Poll every" width="200px" required="true">
            <options>
                <option label="1 minute" value=60/>
                <option label="2 minutes" value=120/>
                <option label="5 minutes" value=300 default="true"/>
                <option label="10 minutes" value=600/>
                <option label="30 minutes" value=1800/>
            </options>
        </param>
        <param field="Mode5" label="Debug mode" width="75px" required="true">
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
    MAX_THERMOSTAT, \
    MAX_THERMOSTAT_PLUS, \
    MAX_WINDOW_SHUTTER, \
    MAX_WALL_THERMOSTAT, \
    MAX_DEVICE_MODE_AUTOMATIC, \
    MAX_DEVICE_MODE_MANUAL, \
    MAX_DEVICE_MODE_VACATION, \
    MAX_DEVICE_MODE_BOOST

class BasePlugin:
    enabled = False
    def __init__(self):
        return

    def setpollinterval(self, target):
        if target > 30:
            self.skipbeats=target/30
            self.beats=self.skipbeats
            Domoticz.Heartbeat(30)
        else:
            self.skipbeats=0
            self.beats=1
            Domoticz.Heartbeat(target)
        
    def onStart(self):
        if Parameters["Mode5"]=="True": 
            Domoticz.Debugging(2)
            DumpConfigToLog()
        self.setpollinterval(int(Parameters["Mode2"]))

        # Read Cube for intialization of devices
        Domoticz.Log("Reading e-Q3 MAX! devices from Cube...")
        cube = MaxCube(MaxCubeConnection(Parameters["Address"], int(Parameters["Port"])))
        for EQ3device in cube.devices:
           # Add devices if required
            deviceFound = False
            for Device in Devices:
                if Devices[Device].DeviceID == EQ3device.rf_address: deviceFound = True
            if (deviceFound == False):
                Domoticz.Log("Adding device(s) for " + EQ3device.name + " Type: " + type + " ID: " + EQ3device.rf_address)
                if cube.is_thermostat(EQ3device):
                    # Create percentage device
                    Domoticz.Device(Name=EQ3device.name + " - Percentage" , Unit=len(Devices)+1, DeviceID=EQ3device.rf_address, Type=243, Subtype=6, Used=1).Create()
                    if Parameters["Mode1"] == "RV":
                        # Create thermostat device
                        Domoticz.Device(Name=EQ3device.name, Unit=len(Devices)+1, DeviceID=EQ3device.rf_address, Type=242, Subtype=1, Used=1).Create()
                        # Create temperature device
                        Domoticz.Device(Name=EQ3device.name + " - Temperature", Unit=len(Devices)+1, DeviceID=EQ3device.rf_address, Type=80, Subtype=5, Used=1).Create()
                if cube.is_wallthermostat(EQ3device):
                    # Create thermostat device
                    Domoticz.Device(Name=EQ3device.name, Unit=len(Devices)+1, DeviceID=EQ3device.rf_address, Type=242, Subtype=1, Used=1).Create()
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
                    Devices[Unit].Update(0,str(Level))

    def onHeartbeat(self):
        #Cancel the rest of this function if this heartbeat needs to be skipped
        if self.beats < self.skipbeats:
            Domoticz.Debug("Skipping heartbeat: " + str(self.beats))
            self.beats += 1
            return
        self.beats=1

        # Read data from Cube
        cube = MaxCube(MaxCubeConnection(Parameters["Address"], int(Parameters["Port"])))

        # Update devices in Domoticz
        for EQ3device in cube.devices:
            if cube.is_thermostat(EQ3device):
                # Look up & update corresponding Domoticz percentage device
                for DomDevice in Devices:
                    if Devices[DomDevice].Type == 243 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                        if Devices[DomDevice].sValue != str(EQ3device.valve_position):
                            Domoticz.Log("Updating value for " + Devices[DomDevice].Name + ": " + str(EQ3device.valve_position) + "%")
                            Devices[DomDevice].Update(0,str(EQ3device.valve_position))
                if Parameters["Mode1"] == "RV":
                    # Look up & update corresponding Domoticz thermostat device
                    for DomDevice in Devices:
                        if Devices[DomDevice].Type == 242 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                            if Devices[DomDevice].sValue != str(EQ3device.target_temperature):
                                Domoticz.Log("Updating value for " + Devices[DomDevice].Name + ": " + str(EQ3device.target_temperature) + "\u00b0C")
                                Devices[DomDevice].Update(0,str(EQ3device.target_temperature))
                    # Look up & update corresponding Domoticz temperature device
                    for DomDevice in Devices:
                        if Devices[DomDevice].Type == 80 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                            if Devices[DomDevice].sValue != str(EQ3device.actual_temperature):
                                Domoticz.Log("Updating value for " + Devices[DomDevice].Name + ": " + str(EQ3device.actual_temperature) + "\u00b0C")
                                Devices[DomDevice].Update(0,str(EQ3device.actual_temperature))
            elif cube.is_wallthermostat(EQ3device):
                # Look up & update corresponding Domoticz thermostat device
                for DomDevice in Devices:
                    if Devices[DomDevice].Type == 242 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                        if Devices[DomDevice].sValue != str(EQ3device.target_temperature):
                            Domoticz.Log("Updating value for " + Devices[DomDevice].Name + ": " + str(EQ3device.target_temperature) + "\u00b0C")
                            Devices[DomDevice].Update(0,str(EQ3device.target_temperature))           
                # Look up & update corresponding Domoticz temperature device
                for DomDevice in Devices:
                    if Devices[DomDevice].Type == 80 and Devices[DomDevice].DeviceID == EQ3device.rf_address:
                        if Devices[DomDevice].sValue != str(EQ3device.actual_temperature):
                            Domoticz.Log("Updating value for " + Devices[DomDevice].Name + ": " + str(EQ3device.actual_temperature) + "\u00b0C")
                            Devices[DomDevice].Update(0,str(EQ3device.actual_temperature))
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
                            Domoticz.Log("Updating value for " + Devices[DomDevice].Name + ": " + svalue)
                            Devices[DomDevice].Update(nvalue,svalue)

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
