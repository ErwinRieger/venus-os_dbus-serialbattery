dbus-serialbattery
===================

My minimal serialbattery driver for venus os, based on version v0.12b3 of https://github.com/Louisvdw/dbus-serialbattery (https://github.com/Louisvdw/dbus-serialbattery/tree/99f3e0bcd9c72be0f049024b0aecb87434a70b6f).

* Removed most bms drivers, just serial-battery and daly bms.
* Removed threads, use glib event handling.
* Fix daly serial port communication.


See original [README on GitHub](https://github.com/Louisvdw/dbus-serialbattery/blob/master/README.md)


