# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import logging
import serial
from time import sleep
from struct import *

# Logging
logging.basicConfig()
logger = logging.getLogger("SerialBattery")
logger.setLevel(logging.INFO)

# Constants - Need to dynamically get them in future
DRIVER_VERSION = 0.12
<<<<<<< HEAD
<<<<<<< HEAD
DRIVER_SUBVERSION = 'b3'
=======
DRIVER_SUBVERSION = ''
>>>>>>> Importing.
zero_char = chr(48)
degree_sign = u'\N{DEGREE SIGN}'
# Cell min/max voltages - used with the cell count to get the min/max battery voltage
MIN_CELL_VOLTAGE = 2.9
<<<<<<< HEAD
MAX_CELL_VOLTAGE = 3.45
# battery Current limits
MAX_BATTERY_CURRENT = 50.0
MAX_BATTERY_DISCHARGE_CURRENT = 60.0
# Charge current control management enable (True/False). 
CCCM_ENABLE = True
# Simulate Midpoint graph (True/False). 
MIDPOINT_ENABLE = False

# Daly settings
# Battery capacity (amps) if the BMS does not support reading it 
BATTERY_CAPACITY = 50
# Invert Battery Current. Default non-inverted. Set to -1 to invert
INVERT_CURRENT_MEASUREMENT = 1
=======
MAX_CELL_VOLTAGE = 3.5
=======
DRIVER_SUBVERSION = 'b3'
zero_char = chr(48)
degree_sign = u'\N{DEGREE SIGN}'


MAX_VOLTAGE_TIME_SEC = 15*60
SOC_LEVEL_TO_RESET_VOLTAGE_LIMIT = 90

>>>>>>> Update serialbattery code, includes our daly.py changes.
# battery Current limits
# MAX_BATTERY_CURRENT = 50.0
MAX_BATTERY_CURRENT = 250.0 # manne: 100
# MAX_BATTERY_DISCHARGE_CURRENT = 60.0
MAX_BATTERY_DISCHARGE_CURRENT = 250.0 # manne: 100


#
# CCCM, CVL, CCL, DCL, CVCL
# 
# Charge current control management enable (True/False). 
CCCM_ENABLE = False
# Charge voltage control management enable (True/False). 
CVCM_ENABLE = True
# Cell min/max voltages - used with the cell count to get the min/max battery voltage
MIN_CELL_VOLTAGE = 3.0
# pv charger control
MAX_CELL_VOLTAGE = 3.45                       # CVCM_ENABLE max charging voltage
# FLOAT_CELL_VOLTAGE = MAX_CELL_VOLTAGE - 0.05  # float cell voltage, note: voltage overshot
FLOAT_CELL_VOLTAGE = MAX_CELL_VOLTAGE - 0.025   # float cell voltage, note: voltage overshot
# Charging cellvoltage when to reconnect inverter (load)
RECONNECTCELLVOLTAGE = 3.275 # 52.4v, about 50% SOC, note: inverter will reconnect at 52v

# Simulate Midpoint graph (True/False). 
MIDPOINT_ENABLE = False

# Daly settings
# Battery capacity (amps) if the BMS does not support reading it 
# BATTERY_CAPACITY = 50
BATTERY_CAPACITY = 450 # manne: 75
# Invert Battery Current. Default non-inverted. Set to -1 to invert
INVERT_CURRENT_MEASUREMENT = -1
>>>>>>> Importing.

# TIME TO SOC settings [Valid values 0-100, but I don't recommend more that 20 intervals]
# Set of SoC percentages to report on dbus. The more you specify the more it will impact system performance.
# TIME_TO_SOC_POINTS = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10, 5, 0]		# Every 5% SoC
# TIME_TO_SOC_POINTS = [100, 95, 90, 85, 75, 50, 25, 20, 10, 0]
TIME_TO_SOC_POINTS = []	# No data set to disable
# Specify TimeToSoc value type: [Valid values 1,2,3]
# TIME_TO_SOC_VALUE_TYPE = 1      # Seconds
# TIME_TO_SOC_VALUE_TYPE = 2      # Time string HH:MN:SC
TIME_TO_SOC_VALUE_TYPE = 3        # Both Seconds and time str "<seconds> [days, HR:MN:SC]"
# Specify how many loop cycles between each TimeToSoc updates
TIME_TO_SOC_LOOP_CYCLES = 5
# Include TimeToSoC points when moving away from the SoC point. [Valid values True,False] 
# These will be as negative time. Disabling this improves performance slightly.
TIME_TO_SOC_INC_FROM = False


# Select the format of cell data presented on dbus. [Valid values 0,1,2,3]
# 0 Do not publish all the cells (only the min/max cell data as used by the default GX)
# 1 Format: /Voltages/Cell# (also available for display on Remote Console)
# 2 Format: /Cell/#/Volts
# 3 Both formats 1 and 2
BATTERY_CELL_DATA_FORMAT = 1

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Update serialbattery code, includes our daly.py changes.
# Settings for ESC GreenMeter and Lipro devices
GREENMETER_ADDRESS = 1
# LIPRO_START_ADDRESS = 2
# LIPRO_END_ADDRESS = 4
LIPRO_CELL_COUNT = 15
<<<<<<< HEAD
=======
>>>>>>> Importing.
=======
>>>>>>> Update serialbattery code, includes our daly.py changes.

def is_bit_set(tmp):
    return False if tmp == zero_char else True

def kelvin_to_celsius(kelvin_temp):
    return kelvin_temp - 273.1

def format_value(value, prefix, suffix):
    return None if value is None else ('' if prefix is None else prefix) + \
                                      str(value) + \
                                      ('' if suffix is None else suffix)

def read_serial_data(command, port, baud, length_pos, length_check, length_fixed=None, length_size=None):
    # try:
    with serial.Serial(port, baudrate=baud, timeout=0.1) as ser:
        return read_serialport_data(ser, command, length_pos, length_check, length_fixed, length_size)

    # except serial.SerialException as e:
        # logger.exception(e)
        # return False


# Open the serial port
# Return variable for the openned port 
def open_serial_port(port, baud):
    return serial.Serial(port, baudrate=baud, timeout=0.1)

    """
    ser = None
    tries = 3
    while tries > 0:
        try:
            ser = serial.Serial(port, baudrate=baud, timeout=0.1)
            tries = 0
        except serial.SerialException as e:
            logger.exception(e)
            tries -= 1
            
    return ser
    """

def read_serial_garbage(ser, when):
    l = ser.inWaiting()
    while l:
        logger.info(f"read_serial_garbage ({when}): {l} bytes available...")
        # try:
        res = ser.read(l)
        # except serial.SerialException as e:
            # logger.exception(e)
            # logger.error(f"read_serial_garbage(): exception while reading, ignoring:")
            # l = ser.inWaiting()
            # continue
        logger.info(f"read_serial_garbage: read {len(res)} bytes ...")
        sleep(0.05)
        l = ser.inWaiting()

# Read data from previously openned serial port
def read_serialport_data(ser, command, length_pos, length_check, length_fixed=None, length_size=None):

    try:
        # ser.flushOutput()
        # ser.flushInput()
        read_serial_garbage(ser, "before");

        ser.write(command)
        ser.flushOutput()

        length_byte_size = 1
        if length_size is not None: 
            if length_size.upper() == 'H':
                length_byte_size = 2
            elif length_size.upper() == 'I' or length_size.upper() == 'L':
                length_byte_size = 4

        count = 0
        toread = ser.inWaiting()

        while toread < (length_pos+length_byte_size):
            sleep(0.005)
            toread = ser.inWaiting()
            count += 1
            if count > 150:
                logger.error(">>> ERROR: No reply - returning")
                return False
                
        #logger.info('serial data toread ' + str(toread))
        res = ser.read(toread)
        if length_fixed is not None:
            length = length_fixed
        else:
            if len(res) < (length_pos+length_byte_size):
                logger.error(">>> ERROR: No reply - returning [len:" + str(len(res)) + "]")
                return False
            length_size = length_size if length_size is not None else 'B'
            length = unpack_from('>'+length_size, res,length_pos)[0]
            
        #logger.info('serial data length ' + str(length))

        count = 0
        data = bytearray(res)
        while len(data) <= length + length_check:
            res = ser.read((length + length_check) - len(data) + 1)
            data.extend(res)
            #logger.info('serial data length ' + str(len(data)))
            sleep(0.005)
            count += 1
            if count > 150:
                logger.error(">>> ERROR: No reply - returning [len:" + str(len(data)) + "/" + str(length + length_check) + "]")
                return False

        sleep(0.05)
        read_serial_garbage(ser, "after");
        return data

    except serial.SerialException as e:
        logger.exception(e)
        logger.error(f"read_serialport_data(): exception caught...")
        raise

def read_serialport_data_fixed(ser, command, length):

    try:
        read_serial_garbage(ser, "before");

        ser.write(command)
        ser.flushOutput()

        count = 0
        data = bytearray()
        while len(data) < length:
            res = ser.read(length - len(data))
            if res:
                data.extend(res)
                # logger.info(f"read {len(data)} of {length} bytes...")
            
            if len(data) == length:
                break

            sleep(0.1)
            count += 1
            if count > 10: # Timeout: 1s
                logger.error(f"timeout, read {len(data)} of {length} bytes")
                return False

        sleep(0.05)
        read_serial_garbage(ser, "after");
        return data

    except serial.SerialException as e:
        logger.exception(e)
        logger.error(f"read_serialport_data_fixed(): exception caught...")
        raise



