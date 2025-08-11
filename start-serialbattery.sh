#!/bin/bash

. /opt/victronenergy/serial-starter/run-service.sh

app="python /data/venus-os_dbus-serialbattery/dbus-serialbattery.py"
args="/dev/$tty"
start $args
