"""
<plugin key="eq3max" name="eQ-3 MAX!" author="mvzut" version="0.6.6" wikilink="https://github.com/mvzut/maxcube-Domoticz-plugin" externallink="https://www.domoticz.com/forum/viewtopic.php?f=34&amp;t=25081">
    <params>
        <param field="Address" label="Cube address" width="110px" required="true" default="192.168.0.1"/>
        <param field="Port" label="Cube port" width="50px" required="true" default="62910"/>
        <param field="Mode1" label="Valve positions" width="230px" required="true">
            <options>
                <option label="Do not create/delete if present" value="False"/>
                <option label="Create devices" value="True" default="true"/>
            </options>
        </param>
        <param field="Mode2" label="Thermostat modes" width="230px" required="true">
            <options>
                <option label="Do not create/delete if present" value="False" default="true"/>
                <option label="Create devices" value="True"/>
            </options>
        </param>
        <param field="Mode3" label="Heat demand switch" width="230px" required="true">
            <options>
                <option label="Do not create/delete if present" value="False" default="true"/>
                <option label="Create" value="True"/>
            </options>
        </param>
        <param field="Mode4" label="Min valve pos for heat demand" width="30px" required="true" default="25"/>
        <param field="Mode5" label="Update every" width="155px" required="true">
            <options>
                <option label="1 minute" value=60/>
                <option label="2 minutes" value=120/>
                <option label="5 minutes (default)" value=300 default="true"/>
                <option label="10 minutes" value=600/>
                <option label="30 minutes" value=1800/>
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
        if Parameters["Mode1"] == "False" and typename == "Valve" or Parameters["Mode2"] == "False" and typename == "Mode":
            DeviceWanted = False

        # Check if device with given deviceid and devicetype is already present
        DeviceFound = False
        for Device in Devices:
            if Devices[Device].DeviceID == deviceid and Devices[Device].Type == devicetype:
                DeviceFound = True
                # Delete found device if not wanted anymore
                if not DeviceWanted:
                    Domoticz.Log("Deleted device " + Devices[Device].Name)
                    Devices[Device].Delete()
                    break

        # If device not found but wanted, create it
        if not DeviceFound and DeviceWanted:
            # Check first available unit ID
            availableID = 1
            if Devices:
                for device in Devices:
                    if device > availableID: break
                    else: availableID += 1
            # Create device
            Domoticz.Device(Name=name + " - " + typename, Unit=availableID, DeviceID=deviceid, Type=devicetype, Subtype=subtype, Switchtype=switchtype, Options=options, Image = image, Used=1).Create()
            if availableID in Devices:
                # Device created
                Domoticz.Log("Created device '" + Parameters["Name"] + " - " + name + " - " + typename + "'")
            else:
                # Device not created!
                Domoticz.Error("Device '" + Parameters["Name"] + " - " + name + " - " + typename + "' could not be created. Is 'Accept new Hardware Devices' enabled under Settings?")


    def UpdateDevice(self, EQ3device, typename):
        # Set default device values
        nvalue = 0
        battery = 255
        # Set device-specific values
        if typename == "Valve":
            if EQ3device.battery: battery = 100-int(EQ3device.battery)*100
            devicetype = 243
            svalue = str(EQ3device.valve_position)
        elif typename == "Thermostat":
            if EQ3device.battery: battery = 100-int(EQ3device.battery)*100
            devicetype = 242
            svalue = str(EQ3device.target_temperature)
        elif typename == "Temperature":
            devicetype = 80
            svalue = str(EQ3device.actual_temperature)
            if svalue == "None": return
        elif typename == "Mode":
            devicetype = 244
            svalue = str(EQ3device.mode * 10)    
        elif typename == "Contact":
            if EQ3device.battery: battery = 100-int(EQ3device.battery)*100
            devicetype = 244
            if EQ3device.is_open == False:
                svalue = "Off"
            elif EQ3device.is_open == True:
                svalue = "On"
                nvalue = 1

        # Find & update device if it matches and if it has changed
        for DOMdevice in Devices:
            if Devices[DOMdevice].Type == devicetype and Devices[DOMdevice].DeviceID == EQ3device.rf_address: # Found!
                if Devices[DOMdevice].sValue != svalue:
                    Domoticz.Log(typename + " (" + Devices[DOMdevice].Name + ")")
                    Devices[DOMdevice].Update(nValue=nvalue, sValue=svalue, BatteryLevel=battery)
                break


    def onStart(self):
        # Set heartbeat
        self.skipbeats=int(Parameters["Mode5"])/30
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
            Domoticz.Error("Error connecting to Cube. Other running MAX! programs may block the communication!")
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

        # Create or delete devices if necessary
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

        # Create or delete heat demand switch if necessary
        if Parameters["Mode3"] == "True" and 255 not in Devices:
            Domoticz.Device(Name="Heat demand", Unit=255, TypeName="Switch", Image=9, Used=1).Create()
            if 255 not in Devices:
                Domoticz.Error("Heat demand switch could not be created. Is 'Accept new Hardware Devices' enabled under Settings?")
            else:
                Domoticz.Log("Created device '" + Parameters["Name"] + " - Heat demand'") 
                Devices[255].Update(nValue=0, sValue="Off")
        elif Parameters["Mode3"] == "False" and 255 in Devices:
            Devices[255].Delete()
            Domoticz.Log("Deleted heat demand switch")

 
    def onCommand(self, Unit, Command, Level, Hue):
        # Update commands for thermostats
        if Devices[Unit].Type == 242 and Devices[Unit].sValue != str(Level):
            Domoticz.Log("Setpoint changed for " + Devices[Unit].Name + ". New setpoint: " + str(Level))
            try:
                cube = MaxCube(MaxCubeConnection(Parameters["Address"], int(Parameters["Port"])))
            except:
                Domoticz.Error("Error connecting to Cube. Other running MAX! programs may block the communication!")
                return
            for EQ3device in cube.devices:
                if Devices[Unit].DeviceID == EQ3device.rf_address:
                    cube.set_target_temperature(EQ3device, Level)
                    Devices[Unit].Update(nValue=0, sValue=str(Level))
                    Devices[Unit].Refresh()

        # Update commands for mode switches
        if Devices[Unit].Type == 244 and Devices[Unit].SubType == 62 and Devices[Unit].sValue != str(Level):
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
            try:
                cube = MaxCube(MaxCubeConnection(Parameters["Address"], int(Parameters["Port"])))
            except:
                Domoticz.Error("Error connecting to Cube. Other running MAX! programs may block the communication!")
                return
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

        self.HeatDemand = 0

        # Read data from Cube
        Domoticz.Debug("Reading e-Q3 MAX! devices from Cube...")
        try:
            cube = MaxCube(MaxCubeConnection(Parameters["Address"], int(Parameters["Port"])))
        except:
            Domoticz.Error("Error connecting to Cube. Other running MAX! programs may block the communication!")
            return

        # Update devices in Domoticz
        for EQ3device in cube.devices:
            Domoticz.Debug("Checking device '" + EQ3device.name + "' in room " + str(EQ3device.room_id))
            if cube.is_thermostat(EQ3device):
                # Check if valve requires heat
                if EQ3device.valve_position > int(Parameters["Mode4"]): self.HeatDemand += 1
                # Update Domoticz devices for radiator valves
                self.UpdateDevice(EQ3device, "Valve")
                if not self.RoomHasThermostat[EQ3device.room_id]:
                    self.UpdateDevice(EQ3device, "Thermostat")
                    self.UpdateDevice(EQ3device, "Temperature")
                    self.UpdateDevice(EQ3device, "Mode")

            elif cube.is_wallthermostat(EQ3device):
                # Update Domoticz devices for wall thermostats
                self.UpdateDevice(EQ3device, "Thermostat")
                self.UpdateDevice(EQ3device, "Temperature")
                self.UpdateDevice(EQ3device, "Mode")

            elif cube.is_windowshutter(EQ3device):
                # Look up & update Domoticz device for contact switches
                self.UpdateDevice(EQ3device, "Contact")

        # Update heat demand switch if necessary
        Domoticz.Debug(str(self.HeatDemand) + " valves require heat")
        if self.HeatDemand > 0 and Parameters["Mode3"] == "True" and 255 in Devices and Devices[255].sValue == "Off":
            Devices[255].Update(nValue=1, sValue="On")
            Domoticz.Log("Heat demand switch turned on")
        elif self.HeatDemand == 0 and Parameters["Mode3"] == "True" and 255 in Devices and Devices[255].sValue == "On":
            Devices[255].Update(nValue=0, sValue="Off")
            Domoticz.Log("Heat demand switch turned off")


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

