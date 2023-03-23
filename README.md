dbus-serialbattery
===================

My minimal serialbattery driver for venus os, based on version v0.12b3 of https://github.com/Louisvdw/dbus-serialbattery.

* Removed most bms drivers, just serial-battery and daly bms.
* Removed threads, use glib event handling.
* Fix daly serial port communication.
* Added cell-voltage based charging/discharging.


See original [README on GitHub](https://github.com/Louisvdw/dbus-serialbattery/blob/master/README.md)


