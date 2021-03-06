# maxcube-Domoticz-plugin
## ELV/EQ-3 MAX! Python plugin for Domoticz

Integrates the ELV/e-Q3 MAX! system into Domoticz (provided a MAX! Cube LAN gateway module is part of the system). Leaning heavily on the work of hackercowboy: https://github.com/hackercowboy/python-maxcube-api

## Features
The following features are currently impemented:
* Automatically creates devices for all your wall mounted thermostats, radiator valves and door/window sensors.
* If a room has a wall thermostat, this will act as setpoint and temperature sensor in that room. Otherwise, thermostats and temperature sensors will be created for every radiator valve. Note that radiator valves only seem to report temperature when one of their other parameters (valve position, setpoint, mode) are changed!
* An optional "heat demand" switch is turned on when at least one of the valves is open (percentage can be configured). This switch can be used in your own scripts to control your boiler.
* Thermostats, temperature sensors and door/window switches are always created. Valve positions and thermostat mode switches are optional. Note that, even if you choose to not create the valve position devices, the heat demand switch will still function!

## Installation
One of the easiest ways to install the plugin is by entering the following commands in a terminal to your machine running Domoticz (at least if this machine is a Raspberry Pi or something similar):

`cd ~/domoticz/plugins`

`git clone https://github.com/mvzut/maxcube-Domoticz-plugin MaxCube`

(or choose your own folder name instead of "MaxCube")

For updating from an existing version, type the following:

`cd ~/domoticz/plugins/MaxCube` (assuming you installed the plugin in this folder)

`git reset --hard`

`git pull`

After installing or updating the plugin, always restart Domoticz. You can find the plugin under Settings > Hardware. Activate the plugin by selecting it from the "Type" drop-down menu, fill in the parameters (explanation see below) and click "Add" (only for first-time installation).

## Configuration

In the configuration screen of the plugin (under Settings > Hardware), the following settings need to be configured:

* Fill in the IP address of your eQ-3 MAX! Cube
* Fill in the port number of your Cube. The default is 62910, there is no need to change this in most cases.
* Select which  device types you want the plugin to create. Note that existing devices *will be deleted* if you select you don't want them anymore!
* Specify the minimum valve percentage for which the heat demand switch should be turned on (1-100)
* Choose a polling time. The default is 5 minutes, shorter periods can sometimes cause problems, the eQ-3 MAX! system doesn't seem to like too much traffic per hour.
* Choose the debug mode, when debugging is on the plugin will be more verbose in the log.


## More info
You can find more information and discussions in this Domoticz forum topic:
https://www.domoticz.com/forum/viewtopic.php?f=34&t=25081. I would prefer it if bugs or problems are reported there, since I don't look at the reported issues on Github as often.

