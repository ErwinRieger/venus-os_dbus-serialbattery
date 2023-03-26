#!/usr/bin/python
# -*- coding: utf-8 -*-

from time import sleep
from dbus.mainloop.glib import DBusGMainLoop
import sys

if sys.version_info.major == 2:
    import gobject
else:
    from gi.repository import GLib as gobject

from dbushelper import DbusHelper
from utils import DRIVER_VERSION, DRIVER_SUBVERSION, logger
import logging
from daly import Daly

logger.info('Starting dbus-serialbattery')

def main():

    def get_battery_type(_port):
        # all the different batteries the driver support and need to test for
        battery_types = [
            Daly(port=_port, baud=9600, address=b"\x40"),
            Daly(port=_port, baud=9600, address=b"\x80"),
        ]

        # try to establish communications with the battery 3 times, else exit
        count = 3
        while count > 0:
            # create a new battery object that can read the battery and run connection test
            for test in battery_types:
                logger.info('Testing ' + test.__class__.__name__)
                if test.test_connection() is True:
                    logger.info('Connection established to ' + test.__class__.__name__)
                    return test

            count -= 1
            sleep(0.5)

        return None

    def get_port():
        # Get the port we need to use from the argument
        if len(sys.argv) > 1:
            return sys.argv[1]
        else:
            # just for MNB-SPI
            logger.info('No Port needed')
            return '/dev/tty/USB9'

    logger.info('dbus-serialbattery v' + str(DRIVER_VERSION) + DRIVER_SUBVERSION)

    port = get_port()
    battery = get_battery_type(port)

    # exit if no battery could be found
    if battery is None:
        logger.error("ERROR >>> No battery connection at " + port)
        sys.exit(1)
    
    battery.log_settings()
    
    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)
    if sys.version_info.major == 2:
        gobject.threads_init()
    mainloop = gobject.MainLoop()

    # Get the initial values for the battery used by setup_vedbus
    helper = DbusHelper(battery)
    
    if not helper.setup_vedbus():
        logger.error("ERROR >>> Problem with battery set up at " + port)
        sys.exit(1)

    # Poll the battery at INTERVAL and run the main loop
    gobject.timeout_add(battery.poll_interval, lambda: helper.publish_battery(mainloop))
    try:
        mainloop.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
