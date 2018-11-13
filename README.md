# maxcube-Domoticz-plugin
## ELV/EQ-3 MAX! Python plugin for Domoticz

Leaning heavily on the work of hackercowboy: https://github.com/hackercowboy/python-maxcube-api

## Features

* Automatically creates devices for all your wall mounted thermostats, radiator valves and door/window sensors.
* If a room has a wall thermostat, this will act as setpoint and temperature sensor in that room. Otherwise, thermostats and temperature sensors will be created for every radiator valve. Note that radiator valves only report temperature when the valves are moving!
* An optional "heat demand" switch is turned on when at least one of the valves is open (percentage can be configured)
* Thermostats, temperature sensors and door/window switches are always created. Valve positions and thermostat mode switches are optional.

## Configuration

* Fill in the IP address of your eQ-3 MAX! Cube
* Fill in the port number of your Cube. The default is 62910, there is no need to change this in most cases
Select which  device types you want the plugin to create. Note that existing devices will be deleted if you select you don't want them anymore!
* Specify the minimum valve percentage for which the heat demand switch should be turned on (1-100)
* Choose a polling time. The default is 5 minutes, shorter periods can sometimes cause problems, the eQ-3 MAX! system doesn't seem to like too much traffic per hour.
* Choose the debug mode, when debugging is on the plugin will be more verbose in the log.


You can find more info and discussions in this Domoticz forum topic:
https://www.domoticz.com/forum/viewtopic.php?f=34&t=25081&p=192854#p192854

