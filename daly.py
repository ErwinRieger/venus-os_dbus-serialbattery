# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from battery import Protection, Battery, Cell
from utils import *
from struct import *

from dbusmonitor import DbusMonitor

import time, os
import traceback

SocStorage = "/data/db/capacity.dat"
SocStorageInterval = 60

class Daly(Battery):

    def __init__(self, port,baud,address):
        super(Daly, self).__init__(port,baud)
        self.charger_connected = None
        self.load_connected = None
        self.command_address = address
        self.cell_min_voltage = None
        self.cell_max_voltage = None
        self.cell_min_no = None
        self.cell_max_no = None
        self.poll_interval = 1000
        self.poll_step = 0
        self.type = self.BATTERYTYPE
<<<<<<< HEAD
=======
        self.currentAvg = 10 * [0]
        self.iavg = 0

        # Mod erri
        self.capacity_remain = BATTERY_CAPACITY # * 0.66 # don't know real capacity
        self.lastSocTime = self.lastSocWrite = time.time()
            
>>>>>>> Importing.
    # command bytes [StartFlag=A5][Address=40][Command=94][DataLength=8][8x zero bytes][checksum]
    command_base = b"\xA5\x40\x94\x08\x00\x00\x00\x00\x00\x00\x00\x00\x81"
    cellvolt_buffer = b"\xA5\x40\x94\x08\x00\x00\x00\x00\x00\x00\x00\x00\x82\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    command_soc = b"\x90"
    command_minmax_cell_volts = b"\x91"
    command_minmax_temp = b"\x92"
    command_fet = b"\x93"
    command_status = b"\x94"
    command_cell_volts = b"\x95"
    command_temp = b"\x96"
    command_cell_balance = b"\x97"
    command_alarm = b"\x98"
    BATTERYTYPE = "Daly"
    LENGTH_CHECK = 4
    LENGTH_POS = 3
    CURRENT_ZERO_CONSTANT = 30000
    TEMP_ZERO_CONSTANT = 40

    def test_connection(self):
        result = False
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Update serialbattery code, includes our daly.py changes.
        try:
            ser = open_serial_port(self.port, self.baud_rate)
            if ser is not None:
                result = self.read_status_data(ser)
                ser.close()
        except:
            pass
<<<<<<< HEAD
=======
        ser = open_serial_port(self.port, self.baud_rate)
        if ser is not None:
            result = self.read_status_data(ser)
            ser.close()
>>>>>>> Importing.
=======
>>>>>>> Update serialbattery code, includes our daly.py changes.

        return result

    def get_settings(self):
        self.capacity = BATTERY_CAPACITY
        self.max_battery_current = MAX_BATTERY_CURRENT
        self.max_battery_discharge_current = MAX_BATTERY_DISCHARGE_CURRENT

        # self.control_discharge_current = self.max_battery_discharge_current
        # self.control_discharge_current = 0.0
        # self.control_discharge_current = None

        try:

            # xxx query initial battery discharge current from inverter
            dummy = {'code': None, 'whenToLog': 'configChange', 'accessLevel': None}
            dbus_tree = {
                    'com.victronenergy.inverter': { '/State': dummy, '/Link/DischargeCurrent': dummy }  ,
            }
            self.dbusmonitor = DbusMonitor(dbus_tree)

            serviceList = self._get_service_having_lowest_instance('com.victronenergy.inverter')
            if not serviceList:
                # Restart process
                logger.info("service com.victronenergy.inverter not registered yet, exiting...")
                sys.exit(0)
            self.vecan_service = serviceList[0]
            logger.info("service of inverter rs6: " +  self.vecan_service)

            self.initial_i = self.dbusmonitor.get_value(self.vecan_service, "/Link/DischargeCurrent")
            logger.info(f"current discharge current setting: {self.initial_i}")
            # if i == None:
                # ## inverter bms lost
                # self.control_discharge_current = 0.0 
            # else:
                # self.control_discharge_current = i

            self.initial_s = self.dbusmonitor.get_value(self.vecan_service, "/State")
            logger.info(f"current inverter state: {self.initial_s}")

            if self.initial_s == 9:
                # inverting
                if self.initial_i == 0.0:
                    return False # restart

                if self.initial_i == None:
                    logger.info(f"switch off inverter...")
                    self.control_discharge_current = 0.0
                else:
                    logger.info(f"set initial discharge current: {self.initial_i}")
                    self.control_discharge_current = self.initial_i

        except:
            logger.info(f"get_settings(): error reading inverter current")
            traceback.print_exc()
            return False

        try:
            self.capacity_remain = float(open(SocStorage).read())
        except:
            logger.info(f"get_settings(): error reading {SocStorage}")

        logger.info(f"get_settings(): start capacity: {self.capacity_remain} Ah")
        return True

    # returns a tuple (servicename, instance)
    def _get_service_having_lowest_instance(self, classfilter=None): 
        services = self._get_connected_service_list(classfilter=classfilter)
        if len(services) == 0: return None
        s = sorted((value, key) for (key, value) in services.items())
        return (s[0][1], s[0][0])

    def _get_connected_service_list(self, classfilter=None):
        services = self.dbusmonitor.get_service_list(classfilter=classfilter)
        # self._remove_unconnected_services(services)
        return services

    def refresh_data(self):
        result = False
        # Open serial port to be used for all data reads instead of openning multiple times 
        ser = open_serial_port(self.port, self.baud_rate)
        if ser is not None:
            result = self.read_soc_data(ser)
            result = result and self.read_fed_data(ser)
<<<<<<< HEAD
<<<<<<< HEAD
            result = result and self.read_cell_voltage_range_data(ser)

            if self.poll_step == 0:
                result = result and self.read_alarm_data(ser)
                result = result and self.read_temperature_range_data(ser)
            elif self.poll_step == 1:
                result = result and self.read_cells_volts(ser)
                            
=======
=======
            result = result and self.read_cell_voltage_range_data(ser)

>>>>>>> Update serialbattery code, includes our daly.py changes.
            if self.poll_step == 0:
                result = result and self.read_alarm_data(ser)
                result = result and self.read_temperature_range_data(ser)
<<<<<<< HEAD
>>>>>>> Importing.
=======
            elif self.poll_step == 1:
                result = result and self.read_cells_volts(ser)
                            
>>>>>>> Update serialbattery code, includes our daly.py changes.
            #else:          # A placeholder to remind this is the last step. Add any additional steps before here
                # This is last step so reset poll_step
                self.poll_step = -1

            self.poll_step += 1
            
            ser.close()

        return result

    def read_status_data(self, ser):
        status_data = self.read_serial_data_daly(ser, self.command_status)
        # check if connection success
        if status_data is False:
            logger.debug("read_status_data")
            return False

        self.cell_count, self.temp_sensors, self.charger_connected, self.load_connected, \
            state, self.cycles = unpack_from('>bb??bhx', status_data)

        self.max_battery_voltage = MAX_CELL_VOLTAGE * self.cell_count
        self.min_battery_voltage = MIN_CELL_VOLTAGE * self.cell_count

        self.hardware_version = "DalyBMS " + str(self.cell_count) + " cells"
        logger.info(self.hardware_version)
        return True

    def read_soc_data(self, ser):
        # Ensure data received is valid
        crntMinValid = -(MAX_BATTERY_DISCHARGE_CURRENT * 2.1)
        crntMaxValid = (MAX_BATTERY_CURRENT * 1.3)
        triesValid = 2
        while triesValid > 0:
            soc_data = self.read_serial_data_daly(ser, self.command_soc)
            # check if connection success
            if soc_data is False:
                return False

            voltage, tmp, current, soc = unpack_from('>hhhh', soc_data)
            current = ((current - self.CURRENT_ZERO_CONSTANT) / -10 * INVERT_CURRENT_MEASUREMENT)
<<<<<<< HEAD
            if crntMinValid < current < crntMaxValid:
=======

            if crntMinValid < current < crntMaxValid:

                self.currentAvg[self.iavg] = current
                current = sum(self.currentAvg) / len(self.currentAvg)

                self.iavg += 1
                if self.iavg == len(self.currentAvg):
                    self.iavg = 0
            
>>>>>>> Importing.
                self.voltage = (voltage / 10)
                self.current = current
                # self.soc = (soc / 10)

                t = time.time()
                capacity_remain = self.capacity_remain  + (current * (t - self.lastSocTime)) / 3600.0 # current negative if discharging
                self.capacity_remain = max( min(self.capacity, capacity_remain), 0) # cap at 100% and 0%
                self.lastSocTime = t

                self.soc = (100 * self.capacity_remain) / self.capacity

                if (t - self.lastSocWrite) > SocStorageInterval:
                    # Store current soc for restart
                    f = open(SocStorage+".new", "w")
                    f.write(f"{self.capacity_remain}")
                    f.close()
                    os.replace(SocStorage+".new", SocStorage)
                    self.lastSocWrite = t

                return True
                
            logger.warning("read_soc_data - triesValid " + str(triesValid))
            triesValid -= 1

        return False

    def read_alarm_data(self, ser):
        alarm_data = self.read_serial_data_daly(ser, self.command_alarm)
        # check if connection success
        if alarm_data is False:
            logger.warning("read_alarm_data")
            return False

        al_volt, al_temp, al_crnt_soc, al_diff, \
            al_mos, al_misc1, al_misc2, al_fault = unpack_from('>bbbbbbbb', alarm_data)

        if al_volt & 48:
            # High voltage levels - Alarm
            self.voltage_high = 2            
        elif al_volt & 15:
            # High voltage Warning levels - Pre-alarm
            self.voltage_high = 1
        else:
            self.voltage_high = 0

        if al_volt & 128:
            # Low voltage level - Alarm
            self.voltage_low = 2
        elif al_volt & 64:
            # Low voltage Warning level - Pre-alarm
            self.voltage_low = 1
        else:
            self.voltage_low = 0

        if al_temp & 2:
            # High charge temp - Alarm
            self.temp_high_charge = 2            
        elif al_temp & 1:
            # High charge temp - Pre-alarm
            self.temp_high_charge = 1
        else:
            self.temp_high_charge = 0

        if al_temp & 8:
            # Low charge temp - Alarm
            self.temp_low_charge = 2            
        elif al_temp & 4:
            # Low charge temp - Pre-alarm
            self.temp_low_charge = 1
        else:
            self.temp_low_charge = 0


        if al_temp & 32:
            # High discharge temp - Alarm
            self.temp_high_discharge = 2            
        elif al_temp & 16:
            # High discharge temp - Pre-alarm
            self.temp_high_discharge = 1
        else:
            self.temp_high_discharge = 0

        if al_temp & 128:
            # Low discharge temp - Alarm
            self.temp_low_discharge = 2            
        elif al_temp & 64:
            # Low discharge temp - Pre-alarm
            self.temp_low_discharge = 1
        else:
            self.temp_low_discharge = 0

        #if al_crnt_soc & 2:
        #    # High charge current - Alarm
        #    self.current_over = 2            
        #elif al_crnt_soc & 1:
        #    # High charge current - Pre-alarm
        #    self.current_over = 1
        #else:
        #    self.current_over = 0

        #if al_crnt_soc & 8:
        #    # High discharge current - Alarm
        #    self.current_over = 2            
        #elif al_crnt_soc & 4:
        #    # High discharge current - Pre-alarm
        #    self.current_over = 1
        #else:
        #    self.current_over = 0

        if al_crnt_soc & 2 or al_crnt_soc & 8:
            # High charge/discharge current - Alarm
            self.current_over = 2            
        elif al_crnt_soc & 1 or al_crnt_soc & 4:
            # High charge/discharge current - Pre-alarm
            self.current_over = 1
        else:
            self.current_over = 0

        if al_crnt_soc & 128:
            # Low SoC - Alarm
            self.soc_low = 2
        elif al_crnt_soc & 64:
            # Low SoC Warning level - Pre-alarm
            self.soc_low = 1
        else:
            self.soc_low = 0
        
        return True

    def read_cells_volts(self, ser):
        if self.cell_count is not None:
            buffer = bytearray(self.cellvolt_buffer)
            buffer[1] = self.command_address[0]   # Always serial 40 or 80
            buffer[2] = self.command_cell_volts[0]

            maxFrame = (int(self.cell_count / 3) + 1)
<<<<<<< HEAD
<<<<<<< HEAD
            lenFixed = (maxFrame * 12) # 0xA5, 0x01, 0x95, 0x08 + 1 byte frame + 6 byte data + 1byte reserved
=======
            lenFixed = (maxFrame * 12)
>>>>>>> Importing.
=======
            lenFixed = (maxFrame * 12) # 0xA5, 0x01, 0x95, 0x08 + 1 byte frame + 6 byte data + 1byte reserved
>>>>>>> Update serialbattery code, includes our daly.py changes.

            cells_volts_data = read_serialport_data(ser, buffer, self.LENGTH_POS, self.LENGTH_CHECK, lenFixed)
            if cells_volts_data is False:
                logger.warning("No cell_volts_data in read_cells_volts")
                return False

            frameCell = [0, 0, 0]
            lowMin = (MIN_CELL_VOLTAGE / 2)
<<<<<<< HEAD
<<<<<<< HEAD
            frame = 0
            bufIdx = 0

            if len(self.cells) != self.cell_count:
                # init the numbers of cells
                self.cells = []
                for idx in range(self.cell_count):
                    self.cells.append(Cell(True))

            while bufIdx < len(cells_volts_data) - 4: # we at least need 4 bytes to extract the identifiers
                b1, b2, b3, b4 = unpack_from('>BBBB', cells_volts_data, bufIdx)
                if b1 == 0xA5 and b2 == 0x01 and b3 == 0x95 and b4 == 0x08:
                  frame, frameCell[0], frameCell[1], frameCell[2] = unpack_from('>Bhhh', cells_volts_data, bufIdx + 4)
                  for idx in range(3):
                    cellnum = ((frame - 1) * 3) + idx  # daly is 1 based, driver 0 based
                    if cellnum >= self.cell_count:
                        break
                    cellVoltage = frameCell[idx] / 1000
                    self.cells[cellnum].voltage = None if cellVoltage < lowMin else cellVoltage
                  bufIdx += 10 # BBBBBhhh -> 11 byte
                bufIdx += 1
=======
            cellnum = 0
            frame = 0
            while frame >= 0 and frame < maxFrame and cellnum < self.cell_count:
                startPos = ((frame * 12) + 4)
                #logger.debug('cell: ' + str(cellnum) + ', startPos: ' + str(startPos) + ', frame: ' + str(frame))
                if frame > 0 and frame < 16:
                    startPos += 1
                frame, frameCell[0], frameCell[1], frameCell[2], reserved = unpack_from('>bhhhb', cells_volts_data, startPos)
                for idx in range(3):
                    if len(self.cells) == cellnum:
                        self.cells.append(Cell(True))
                    self.cells[cellnum].voltage = None if frameCell[idx] < lowMin else (frameCell[idx] / 1000)
                    cellnum += 1
>>>>>>> Importing.
=======
            frame = 0
            bufIdx = 0

            if len(self.cells) != self.cell_count:
                # init the numbers of cells
                self.cells = []
                for idx in range(self.cell_count):
                    self.cells.append(Cell(True))

            while bufIdx < len(cells_volts_data) - 4: # we at least need 4 bytes to extract the identifiers
                b1, b2, b3, b4 = unpack_from('>BBBB', cells_volts_data, bufIdx)
                if b1 == 0xA5 and b2 == 0x01 and b3 == 0x95 and b4 == 0x08:
                  frame, frameCell[0], frameCell[1], frameCell[2] = unpack_from('>Bhhh', cells_volts_data, bufIdx + 4)
                  for idx in range(3):
                    cellnum = ((frame - 1) * 3) + idx  # daly is 1 based, driver 0 based
                    if cellnum >= self.cell_count:
                        break
                    cellVoltage = frameCell[idx] / 1000

                    # logger.info(f"Read cell voltage: {cellVoltage}")

                    self.cells[cellnum].voltage = None if cellVoltage < lowMin else cellVoltage
                  bufIdx += 10 # BBBBBhhh -> 11 byte
                bufIdx += 1
>>>>>>> Update serialbattery code, includes our daly.py changes.

        return True

    def read_cell_voltage_range_data(self, ser):
        minmax_data = self.read_serial_data_daly(ser, self.command_minmax_cell_volts)
        # check if connection success
        if minmax_data is False:
            logger.warning("read_cell_voltage_range_data")
            return False

        cell_max_voltage,self.cell_max_no,cell_min_voltage, self.cell_min_no = unpack_from('>hbhb', minmax_data)
        # Daly cells numbers are 1 based and not 0 based
        self.cell_min_no -= 1
        self.cell_max_no -= 1
        # Voltage is returned in mV
        self.cell_max_voltage = cell_max_voltage / 1000
        self.cell_min_voltage = cell_min_voltage / 1000
        return True

    def read_temperature_range_data(self, ser):
        minmax_data = self.read_serial_data_daly(ser, self.command_minmax_temp)
        # check if connection success
        if minmax_data is False:
            logger.debug("read_temperature_range_data")
            return False

        max_temp,max_no,min_temp, min_no = unpack_from('>bbbb', minmax_data)
        self.temp1 = min_temp - self.TEMP_ZERO_CONSTANT
        self.temp2 = max_temp - self.TEMP_ZERO_CONSTANT
        return True

    def read_fed_data(self, ser):
        fed_data = self.read_serial_data_daly(ser, self.command_fet)
        # check if connection success
        if fed_data is False:
            logger.debug("read_fed_data")
            return False

        status, self.charge_fet, self.discharge_fet, bms_cycles, capacity_remain = unpack_from('>b??BL', fed_data)
        # mod erri does not work?
        # self.capacity_remain = capacity_remain / 1000
        return True

    def generate_command(self, command):
        buffer = bytearray(self.command_base)
        buffer[1] = self.command_address[0]   # Always serial 40 or 80
        buffer[2] = command[0]
        buffer[12] = sum(buffer[:12]) & 0xFF   #checksum calc
        return buffer

    def read_serial_data_daly(self, ser, command):
        data = read_serialport_data(ser, self.generate_command(command), self.LENGTH_POS, self.LENGTH_CHECK)
        if data is False:
            return False

        start, flag, command_ret, length = unpack_from('BBBB', data)
        checksum = sum(data[:-1]) & 0xFF

        if start == 165 and length == 8 and checksum == data[12]:
            return data[4:length+4]
        else:
            logger.error(">>> ERROR: Incorrect Reply")
            return False
