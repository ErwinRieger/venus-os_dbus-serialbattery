# -*- coding: utf-8 -*-

import math, time, random
from datetime import timedelta

# import libup

#
# eve standard charge:
# * 0.5C charging current
# * 3.65V charging voltage
# * 0.05C cut off current
#
THTime = 60 # [s]

from utils import *

C50 = BATTERY_CAPACITY / 2
CUTOFFCURR = BATTERY_CAPACITY*0.05 # [A]

logger.info(f"CUTOFFCURR: {CUTOFFCURR}")

class ValueTimer(object):
    def __init__(self, name, th_secs):
        self.name = name
        self.th = th_secs
        self._ok = False
        self.reset()
    def add(self, v):
        if not self.value:
            logger.info(f"state {self.name}: begin counting")
        self.value += v
        if not self._ok and self.value > self.th:
            logger.info(f"state of value {self.name} changed to True ({self.value}s)")
            self._ok = True
    def ok(self):
        return self._ok
    def reset(self):
        if self._ok:
            logger.info(f"state of value {self.name} changed to False ({self.value}s)")
            self._ok = False
        self.value = 0
    def stateStr(self):
        return f"{self.value}/{self.th}"

class State(object):
    def __init__(self, name):
        self.name = name

# Error cell-voltage from bms
measureoffs = 0.005
# u0 = 3.375 # i=0
cellu0 = 3.37 + measureoffs
umax = 3.60 # 3.65, i=0.5C

cellpull = cellu0 + 0.005
cellfloat = cellu0 - 0.005

vrange = umax - cellpull

MAX_CHARGING_CELL_VOLTAGE = 3.55

STATEBULK  = 0
STATEBAL   = 1
STATESINK  = 2
STATEFLOAT = 3

class StateBulk(State):

    def __init__(self):
        super(StateBulk, self).__init__("bulkCharging")
        self.cc = ValueTimer(f"T-Cutoff", THTime)

    def run(self, battery):
        # change state if:
        # * charging current is in CUTOFFCURR window
        if abs(battery.current) <= CUTOFFCURR and battery.get_max_cell_voltage() >= cellpull:
            self.cc.add(battery.poll_interval/1000)
        else:
            self.cc.reset()

        if self.cc.ok():
            # Switch to balancing state
            logger.info(f"Bulk state: switching to balancing after {self.cc.value} seconds")
            battery.chargerSM.setState(STATEBAL)

    def bcv(self, battery):
        # bulk, dynamic charging voltage, depends on charging-current
        # bcv = max(3.45, 3.40 + (3.6-3.40) * round( battery.current / C50 , 2))
        bcv = max(
                cellpull,
                min( cellpull + vrange * round( battery.current / C50 , 2), MAX_CHARGING_CELL_VOLTAGE )
                )
        return bcv

    def stateId(self):
        return STATEBULK

    def reset(self):
        self.cc.reset()

    def stateStr(self):
        return f"Bulk-state, t-cutoff: {self.cc.stateStr()}s"

class StateBal(State):

    def __init__(self):
        super(StateBal, self).__init__("stateBalancing")
        self.baltime = ValueTimer("BalanceTime", BALANCETIME)
        self.dsctime = ValueTimer("Discharging", THTime)

    def isBalanced(self):
        # xxx debug remove
        # return True
        return self.baltime.ok()

    def run(self, battery):
        # change state if:
        # * cell-diff is below threshold for BalanceTime seconds
        minCellVoltage = battery.get_min_cell_voltage()
        maxCellVoltage = battery.get_max_cell_voltage()
        cellDiff = maxCellVoltage - minCellVoltage

        if cellDiff < 0.005:
            # logger.info("celldiff:", cellDiff)
            self.baltime.add(battery.poll_interval/1000)

        if self.isBalanced():
            # Switch to float-sink state
            logger.info(f"Balancing state: switching to float-sink, balanced time: {self.baltime.value} seconds")
            battery.chargerSM.setState(STATESINK)
        else:
            # if battery.get_min_cell_voltage() < 3.375:
            # charging current is in CUTOFFCURR window
            if abs(battery.current) > CUTOFFCURR or battery.get_max_cell_voltage() < cellpull:
                self.dsctime.add(battery.poll_interval/1000)
            else:
                self.dsctime.reset()

            if self.dsctime.ok():
                # Switch to bulk state
                logger.info(f"Balance state: switching to bulk after {self.dsctime.value} seconds discharge")
                battery.chargerSM.setState(STATEBULK)

    def bcv(self, battery):
        return cellpull

    def stateId(self):
        return STATEBAL

    def reset(self):
        self.dsctime.reset()

    def resetDayly(self):
        self.baltime.reset()

    def stateStr(self):
        return f"Balancing-state, t-balance: {self.baltime.stateStr()}s, t-discharge: {self.dsctime.stateStr()}s"

class StateSink(State):

    def __init__(self):
        super(StateSink, self).__init__("stateSink")

    def run(self, battery):

        if battery.get_min_cell_voltage() <= cellfloat:
            logger.info(f"Float-Sink state: switching to float, cellfloat: {cellfloat} ...")
            battery.chargerSM.setState(STATEFLOAT)

    def bcv(self, battery):
        return cellfloat

    def stateId(self):
        return STATESINK

    def reset(self):
        pass

    def stateStr(self):
        return f"Sink-state"

class StateFloat(State):

    def __init__(self):
        super(StateFloat, self).__init__("stateFloat")
        self.dsctime = ValueTimer("Discharging", THTime)

    def run(self, battery):

        if battery.get_max_cell_voltage() < cellfloat:
            self.dsctime.add(battery.poll_interval/1000)
        else:
            self.dsctime.reset()

        if self.dsctime.ok():
            # Switch to bulk state
            logger.info(f"Float state: switching to bulk after {self.dsctime.value} seconds discharge")
            battery.chargerSM.setState(STATEBULK)

    def bcv(self, battery):
        return cellfloat

    def stateId(self):
        return STATEFLOAT

    def reset(self):
        self.dsctime.reset()

    def stateStr(self):
        return f"Float-state, t-discharge: {self.dsctime.stateStr()}s"

class ChgStateMachine(object):

    def __init__(self, name):
        self.name = name
        self.state = STATEBULK

        self.states = [
            StateBulk(),
            StateBal(),
            StateSink(),
            StateFloat(),
        ]

    def run(self, battery):
        self.getState().run(battery)

    def bcv(self, battery):
        return self.getState().bcv(battery)

    def setState(self, state):

        s = self.states[state]

        logger.info(f"ChgStatemachine: {self.getState().name} -> {s.name}")

        s.reset()
        self.state = state

    def getState(self, s=None):

        if s!=None:
            return self.states[s]

        return self.states[self.state]

    def stateStr(self):
        return self.getState().stateStr()

class Protection(object):
    # 2 = Alarm, 1 = Warning, 0 = Normal
    def __init__(self):
        self.voltage_high = None
        self.voltage_low = None
        self.voltage_cell_low = None
        self.soc_low = None
        self.current_over = None
        self.current_under = None
        self.cell_imbalance = None
        self.internal_failure = None
        self.temp_high_charge = None
        self.temp_low_charge = None
        self.temp_high_discharge = None
        self.temp_low_discharge = None


class Cell:
    voltage = None
    balance = None

    def __init__(self, balance):
        self.balance = balance


class Battery(object):

    def __init__(self, port, baud):
        self.port = port
        self.baud_rate = baud
        self.role = 'battery'
        self.type = 'Generic'
        self.poll_interval = 1000 # mS
        self.online = True

        self.hardware_version = None
        self.voltage = None
        self.current = None
        self.capacity_remain = None
        self.capacity = None
        self.cycles = None
        self.total_ah_drawn = None

        self.production = None
        self.protection = Protection()
        self.version = None
        self.soc = None
        self.charge_fet = None
        self.discharge_fet = None
        self.cell_count = None
        self.temp_sensors = None
        self.temp1 = None
        self.temp2 = None
        self.cells = []
        self.control_voltage = None
        self.control_discharge_current = None # xxx remove me: not set in daly.py:get_settings()
        self.timeToGo = 0
        self.control_charge_current = None
        self.control_allow_charge = None
        self.control_allow_discharge = None
        # max battery charge/discharge current
        self.max_battery_current = None
        self.max_battery_discharge_current = C50 # initial value
        
        self.time_to_soc_update = TIME_TO_SOC_LOOP_CYCLES

        # charging/balancing
        # XXX unterscheidung verschiedene balancer !!!!!!!!!!!!!
        self.balancing = False
        self.throttling = None

        self.chargerSM = ChgStateMachine("ChargerStateMachine")
        self.chargerSM.setState(STATEBULK)

        self.dbgcount = 3570

        self.forceMode = 0 # 1: force discharge/inverter on, -1: force discharge/inverter off

    def test_connection(self):
        # Each driver must override this function to test if a connection can be made
        # return false when fail, true if successful
        return False

    def get_settings(self):
        # Each driver must override this function to read/set the battery settings
        # It is called once after a successful connection by DbusHelper.setup_vedbus()
        # Values:  battery_type, version, hardware_version, min_battery_voltage, max_battery_voltage,
        #   MAX_BATTERY_CURRENT, MAX_BATTERY_DISCHARGE_CURRENT, cell_count, capacity
        # return false when fail, true if successful
        return False

    def refresh_data(self):
        # Each driver must override this function to read battery data and populate this class
        # It is called each poll just before the data is published to vedbus
        # return false when fail, true if successful
        return False

    def to_temp(self, sensor, value):
        # Keep the temp value between -20 and 100 to handle sensor issues or no data.
        # The BMS should have already protected before those limits have been reached.
        if sensor == 1:
            self.temp1 = min(max(value, -20), 100)
        if sensor == 2:
            self.temp2 = min(max(value, -20), 100)

    def manage_charge_voltage(self):
        voltageSum = 0
        if (CVCM_ENABLE):

            """
            if len(self.cells) < self.cell_count:
                # Handle case when not all data is available on startup
                logger.info(f"incomplete cell data...: {len(self.cells)} of {self.cell_count}")
                return
            """

            minCellVoltage = self.get_min_cell_voltage()
            maxCellVoltage = self.get_max_cell_voltage()
            cellDiff = maxCellVoltage - minCellVoltage

            # logger.info(f"Batt voltage (sum): {voltageSum:.3f}V, cell-low: {minCellVoltage:.3f}V, cell-high: {maxCellVoltage:.3f}, diff: {(maxCellVoltage-minCellVoltage)*1000:.2f}mV")

            # disconnect from battery if a cell voltage is below min voltage
            if minCellVoltage < MIN_CELL_VOLTAGE:

                # turn off inverter
                if self.timeToGo:
                    logger.info(f"turn off inverter, cell-low {minCellVoltage:.3f}V < MIN_CELL_VOLTAGE: {MIN_CELL_VOLTAGE:.3f}V")
                self.timeToGo = 0
                self.control_allow_discharge = False

            # re-connect to battery if all cells are above min voltage
            elif minCellVoltage > RECONNECTCELLVOLTAGE:

                # turn on inverter
                if not self.timeToGo:
                    logger.info(f"turn on inverter, cell-low {minCellVoltage:.3f}V > RECONNECTCELLVOLTAGE: {RECONNECTCELLVOLTAGE:.3f}V")
                self.timeToGo = 1
                self.control_allow_discharge = True
            # else:
                # logger.info(f"keep inverter, MIN_CELL_VOLTAGE: {MIN_CELL_VOLTAGE:.3f}V < cell-low {minCellVoltage:.3f}V < RECONNECTCELLVOLTAGE: {RECONNECTCELLVOLTAGE:.3f}V")

            if self.forceMode:
                if (self.forceMode == 1) and (minCellVoltage > MIN_CELL_VOLTAGE):
                    if not self.timeToGo:
                        logger.info(f"forcing discharge/inverter on, cell-low: {minCellVoltage:.3f}V")
                    self.timeToGo = 1
                    self.control_allow_discharge = True
                elif (self.forceMode == -1):
                    if self.timeToGo:
                        logger.info(f"forcing discharge/inverter off")
                    self.timeToGo = 0
                    self.control_allow_discharge = False

                self.forceMode = 0

            ###################################################
            self.chargerSM.run(self)
            bcv = self.chargerSM.bcv(self)
            ###################################################

            aboveVolt = 0
            for cell in self.cells:
                voltage = cell.voltage
                voltageSum+=voltage
                if voltage > bcv:
                    aboveVolt += voltage - bcv

            # Reset balancing state at midnight
            if time.localtime().tm_hour == 0:
                self.chargerSM.getState(STATEBAL).resetDayly()

            self.balancing = self.chargerSM.state == ChgStateMachine.STATEBAL

            self.chgmode = self.chargerSM.state

            balanced = self.chargerSM.getState(STATEBAL).isBalanced()

            if self.control_voltage == None:
                # Initial case
                chargevoltage = voltageSum
            else:
                chargevoltage = self.control_voltage

            # charging algo
            if maxCellVoltage < bcv:
                chargevoltage = bcv * self.cell_count
                self.throttling = False
            elif self.chargerSM.state == STATEFLOAT:
                chargevoltage = bcv * self.cell_count
                self.throttling = True
            else: # maxCellVoltage >= bcv
                if aboveVolt > 0.025: # allow for 25mV hysteresis to avoid frequent voltage changes
                    chargevoltage = min(voltageSum - aboveVolt, self.cell_count * bcv)
                self.throttling = True

            if (chargevoltage != self.control_voltage) or (self.dbgcount == 3600):
                logger.info(f"{self.chargerSM.stateStr()}, {self.current:.1f}A, cellhigh: {maxCellVoltage:.3f}V, above: {aboveVolt:.3f}V, bcv: {bcv:.3f}V, cv: {chargevoltage:.3f}V, bal: {self.balancing}, balanced: {balanced}")
                if self.dbgcount == 3600:
                    self.dbgcount = 0

            self.control_voltage = chargevoltage

            self.dbgcount += 1
            return

    def manage_charge_current(self):
        # If disabled make sure the default values are set and then exit
        if (not CCCM_ENABLE):
            self.control_charge_current = self.max_battery_current
            self.control_discharge_current = self.max_battery_discharge_current
            self.control_allow_charge = True
            return

        # Start with the current values

        # Change depending on the SOC values
        if self.soc is None:
            # Prevent serialbattery from terminating on error
            return False
            
        if self.soc > 99:
            self.control_allow_charge = False
        else:
            self.control_allow_charge = True
        # Change depending on the SOC values
        if 98 < self.soc <= 100:
            self.control_charge_current = 5
        elif 95 < self.soc <= 98:
            self.control_charge_current = self.max_battery_current/4
        elif 91 < self.soc <= 95:
            self.control_charge_current = self.max_battery_current/2
        else:
            self.control_charge_current = self.max_battery_current

        # Dischange depending on the SOC values
        if self.soc <= 10:
            self.control_discharge_current = 5
        elif 10 < self.soc <= 20:
            self.control_discharge_current = self.max_battery_discharge_current/4
        elif 20 < self.soc <= 30:
            self.control_discharge_current = self.max_battery_discharge_current/2
        else:
            self.control_discharge_current = self.max_battery_discharge_current

    def get_min_cell(self):
        min_voltage = 9999
        min_cell = None
        if len(self.cells) == 0 and hasattr(self, 'cell_min_no'):
            return self.cell_min_no

        for c in range(min(len(self.cells), self.cell_count)):
            if self.cells[c].voltage is not None and min_voltage > self.cells[c].voltage:
                min_voltage = self.cells[c].voltage
                min_cell = c
        return min_cell

    def get_max_cell(self):
        max_voltage = 0
        max_cell = None
        if len(self.cells) == 0 and hasattr(self, 'cell_max_no'):
            return self.cell_max_no

        for c in range(min(len(self.cells), self.cell_count)):
            if self.cells[c].voltage is not None and max_voltage < self.cells[c].voltage:
                max_voltage = self.cells[c].voltage
                max_cell = c
        return max_cell

    def get_min_cell_desc(self):
        cell_no = self.get_min_cell()
        return cell_no if cell_no is None else 'C' + str(cell_no + 1)

    def get_max_cell_desc(self):
        cell_no = self.get_max_cell()
        return cell_no if cell_no is None else 'C' + str(cell_no + 1)

    def get_cell_voltage(self, idx):
        if idx>=min(len(self.cells), self.cell_count):
          return None
        return self.cells[idx].voltage
 
    def get_cell_balancing(self, idx):
        if idx>=min(len(self.cells), self.cell_count):
          return None
        if self.cells[idx].balance is not None and self.cells[idx].balance:
          return 1
        return 0

    def get_capacity_remain(self):
        if self.capacity_remain is not None:
            return self.capacity_remain
        if self.capacity is not None and self.soc is not None:
            return self.capacity * self.soc / 100
        return None

    def get_timetosoc(self, socnum, crntPrctPerSec):
        if self.current > 0:
            diffSoc = (socnum - self.soc)
        else:
            diffSoc = (self.soc - socnum)

        ttgStr = None
        if self.soc != socnum and (diffSoc > 0 or TIME_TO_SOC_INC_FROM is True):
            secondstogo = int(diffSoc / crntPrctPerSec)
            ttgStr = ""

            if (TIME_TO_SOC_VALUE_TYPE & 1):
                ttgStr += str(secondstogo)
                if (TIME_TO_SOC_VALUE_TYPE & 2):
                    ttgStr += " ["
            if (TIME_TO_SOC_VALUE_TYPE & 2):
                ttgStr += str(timedelta(seconds=secondstogo))
                if (TIME_TO_SOC_VALUE_TYPE & 1):
                    ttgStr += "]"
                    
        return ttgStr

    
    def get_min_cell_voltage(self):
        min_voltage = None
        if hasattr(self, 'cell_min_voltage'):
            min_voltage = self.cell_min_voltage

        if min_voltage is None:
            try:
                min_voltage = min(c.voltage for c in self.cells if c.voltage is not None)
            except ValueError:
                pass
        return min_voltage

    def get_max_cell_voltage(self):
        max_voltage = None
        if hasattr(self, 'cell_max_voltage'):
            max_voltage = self.cell_max_voltage

        if max_voltage is None:
            try:
                max_voltage = max(c.voltage for c in self.cells if c.voltage is not None)
            except ValueError:
                pass
        return max_voltage

    def get_midvoltage(self):
        if not MIDPOINT_ENABLE or self.cell_count is None or self.cell_count == 0 or self.cell_count < 4 or len(self.cells) != self.cell_count:
            return None, None

        halfcount = int(math.floor(self.cell_count/2))
        half1voltage = 0
        half2voltage = 0
        
        try:
            half1voltage = sum(c.voltage for c in self.cells[:halfcount] if c.voltage is not None)
            half2voltage = sum(c.voltage for c in self.cells[halfcount:halfcount*2] if c.voltage is not None)
        except ValueError:
            pass
        
        try:
            # handle uneven cells by giving half the voltage of the last cell to half1 and half2
            extra = 0 if (2*halfcount == self.cell_count) else self.cells[self.cell_count-1].voltage/2
            # get the midpoint of the battery
            midpoint = (half1voltage + half2voltage)/2 + extra 
            return midpoint, (half2voltage-half1voltage)/(half2voltage+half1voltage)*100
        except ValueError:
            return None, None

    def get_balancing(self):

        return self.balancing

        for c in range(min(len(self.cells), self.cell_count)):
            if self.cells[c].balance is not None and self.cells[c].balance:
                return 1
        return 0

    def get_temp(self):
        if self.temp1 is not None and self.temp2 is not None:
            return round((float(self.temp1) + float(self.temp2)) / 2, 2)
        if self.temp1 is not None and self.temp2 is None:
            return round(float(self.temp1) , 2)
        if self.temp1 is None and self.temp2 is not None:
            return round(float(self.temp2) , 2)
        else:
            return None

    def get_min_temp(self):
        if self.temp1 is not None and self.temp2 is not None:
            return min(self.temp1, self.temp2)
        if self.temp1 is not None and self.temp2 is None:
            return self.temp1
        if self.temp1 is None and self.temp2 is not None:
            return self.temp2
        else:
            return None

    def get_max_temp(self):
        if self.temp1 is not None and self.temp2 is not None:
            return max(self.temp1, self.temp2)
        if self.temp1 is not None and self.temp2 is None:
            return self.temp1
        if self.temp1 is None and self.temp2 is not None:
            return self.temp2
        else:
            return None

    def log_cell_data(self):
        if logger.getEffectiveLevel() > logging.INFO and len(self.cells) == 0:
            return False

        cell_res = ""
        cell_counter = 1
        for c in self.cells:
            cell_res += "[{0}]{1}V ".format(cell_counter, c.voltage)
            cell_counter = cell_counter + 1
        logger.debug("Cells:" + cell_res)
        return True

    def log_settings(self):
        
        logger.info(f'Battery connected to dbus from {self.port}')
        logger.info(f'=== Settings ===')
        cell_counter = len(self.cells)
        logger.info(f'> Connection voltage {self.voltage}V | current {self.current}A | SOC {self.soc}%')
        logger.info(f'> Cell count {self.cell_count} | cells populated {cell_counter}')
        logger.info(f'> CCL Charge {self.max_battery_current}A | DCL Discharge {self.max_battery_discharge_current}A')
        logger.info(f'> MIN_CELL_VOLTAGE {MIN_CELL_VOLTAGE}V | MAX_CELL_VOLTAGE {MAX_CELL_VOLTAGE}V')
  
        return









if __name__ == "__main__":
    b = Battery("xport", 999)
    b.current = 350 #CUTOFFCURR + 5
    b.cell_count = 16
    print(b)

    i = 0
    while True:

        if b.chargerSM.state == STATEBULK:
            b.cell_min_voltage = 3.450
            b.cell_max_voltage = b.cell_min_voltage + random.randrange(3, 7)/1000 
            # print(f"batt: cell_min_voltage: {b.cell_min_voltage}")
            # print(f"batt: cell_max_voltage: {b.cell_max_voltage}")
            if b.current > 0:
                b.current = max(0, b.current-25)

        # print(f"batt: cur: {b.current}")

        if b.chargerSM.state == STATEBAL:
            b.cell_min_voltage = 3.399
            b.cell_max_voltage = b.cell_min_voltage + random.randrange(3, 7)/1000 
            # print(f"batt: cell_min_voltage: {b.cell_min_voltage}")
            # print(f"batt: cell_max_voltage: {b.cell_max_voltage}")

        if b.chargerSM.state == STATEFLOAT:
            b.cell_min_voltage -= 0.025
            b.cell_max_voltage -= 0.025
            # print(f"batt: cell_min_voltage: {b.cell_min_voltage}")
            # print(f"batt: cell_max_voltage: {b.cell_max_voltage}")

        # b.chargerSM.run(b)
        b.manage_charge_voltage()

        bcv = b.chargerSM.getState().bcv(b)

        print(f"    *** batt: cur: {b.current}, bcv: {bcv}, balancer on: {b.balancing}, i: {i} ***")

        if i == 45:
            b.chargerSM.getState(ChgStateMachine.STATEBAL).resetDayly()

        time.sleep(0.5)
        i += 1









