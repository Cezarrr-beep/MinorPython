import sys
import os
import copy
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from settings.constants import *
from helpers.helpers import *

# external classes
from ev.evsim import *

import math
import random

pmax   = [ 1000,  1000,   4000];
pmin   = [    0,     0,      0];
cap    = [   30,    20,     70];
soc    = [    0,   1.5,      6];

class EV():
    def __init__(self, pmax, pmin, cap, soc, idx):
        self.evcapacity = cap
        self.evpmax = pmax
        self.evpmin = pmin

        # Static Charging session duration
        self.evenergy = 5+(idx%5)					# Energy demand in kWh per driving session
        self.evminsoc =	self.evenergy 				# Minimum SoC to reach after each session (because of driving)
        self.evconnectiontime = self.evenergy + 2 	# Hours the EV is connected
        self.evarrivalhour = 12+(idx%7)				# Hour of arrival of the EV each day
        self.evsoc = self.evcapacity

        print(' ')
        print('------------------------------------------------------------------------------')
        print('-  EV parameters: pmin='+str(self.evpmin)+', pmax='+str(self.evpmax)+', soc='+str(self.evsoc)+', minsoc='+str(self.evminsoc)+', capacity='+str(self.evcapacity))
        print('-  EV trip parameters: arrival='+str(self.evarrivalhour)+':00, connected='+str(self.evconnectiontime)+'h, driving session='+str(self.evenergy)+'kWh')
        print('------------------------------------------------------------------------------')


        # Disabling trips
        print('== tests without taking into account trip parameters ==')
        self.testtrips = False

        # Test constant charging
        print('Testing constant charging')
        for p in [10,1000,2000,4000,8000,20000]:
            planning = [p] * cfg_sim['intervals']
            self.execute(planning)


        # Test constant discharging
        print('Testing constant discharging (invalid)')
        for p in [10,1000,2000,4000,8000,20000]:
            planning = [-p] * cfg_sim['intervals']
            self.execute(planning)

        # Periodic
        print('Testing periodic charging/discharging')
        for T in range(1,7):
            planning = []
            for i in range(0, cfg_sim['intervals'] ):
                planning.append(T*1000*math.sin(((i*T)/cfg_sim['intervals'])*2*math.pi))
            self.execute(planning)


        print('== tests taking into account trip parameters ==')
        self.testtrips = True

        # Test constant charging
        print('Testing constant charging');
        planning = [20000] * cfg_sim['intervals']
        self.execute(planning)


    # Simulation code
    def execute(self, planning):
        self.evsoc = self.evcapacity

        # pre validation
        if not self.verify_input():
            print("The input parameters for device are invalid! Aborting! Most likely you have not added (enough) values to the profile list using profile.append(<value>).")
            exit()

        # Perform the simulation
        returnprofile = self.simulate(copy.deepcopy(planning))
        if not self.verify_result(returnprofile, planning):
            print("The simulation of device failed! Aborting! Most likely you are violating our constraints. Carefully read the error log above and the comments in the code that caused the crash.")
            exit()


    # Simulation code
    def simulate(self, planning=[]):
        return evsim(copy.deepcopy(self), copy.deepcopy(planning))

    # Function to verify the created planning by the optimization code
    # But also to verify user input, is it valid input?
    def verify_input(self):
        assert (self.evcapacity >= 0)	# The EV capacity must be positive
        assert (self.evminsoc >= 0)		# The minumum EV SoC must be positive
        assert (self.evsoc >= 0)		# The EV SoC must be positive
        assert (self.evsoc <= self.evcapacity)		# The EV SoC may not exceed the capacity
        assert (self.evminsoc <= self.evcapacity)	# The minimum EV SoC may not exceed the capacity
        assert (self.evpmin <= self.evpmax)			# The minimum power must be lower than the maximum power
        return True


    # Function to verify if the code functions correctly
    def verify_result(self, profile, planning):
        # Internal conversion to Wtau
        assert (len(profile) == len(planning))	# The power profile list must be as long as the number of simulation time intervals

        capacity = 1000 * (3600 / cfg_sim['timebase']) * self.evcapacity
        soc = 1000 * (3600 / cfg_sim['timebase']) * self.evsoc
        minsoc = 1000 * (3600 / cfg_sim['timebase']) * self.evminsoc

        intervals_per_day = (3600 / cfg_sim['timebase']) * 24
        intervals_per_hour = (3600 / cfg_sim['timebase'])


        for i in range(0, len(profile)):
            # check availability:
            arrival_day = math.floor(i / intervals_per_day)
            arrival_interval = int(arrival_day * intervals_per_day + self.evarrivalhour * intervals_per_hour)
            departure_interval = int(arrival_interval + self.evconnectiontime * intervals_per_hour)

            # Check for overruns:
            if self.evarrivalhour + self.evconnectiontime >= 24:
                if departure_interval - (24 * (3600 / cfg_sim['timebase'])) >= i and arrival_interval - (
                        24 * (3600 / cfg_sim['timebase'])) > 0:
                    departure_interval -= int(24 * (3600 / cfg_sim['timebase']))
                    arrival_interval -= int(24 * (3600 / cfg_sim['timebase']))

            value = profile[i]


            # -- Verification with trips
            if self.testtrips:
                # Reduce SOC upon arrival
                if i == arrival_interval:
                    soc -= self.evenergy * 1000 * (3600 / cfg_sim['timebase'])
                    assert(soc >= -0.001)	# The EV SoC must be always positive. Your simulation code resulted in a negative SoC. Are you charging enough power?

                if i >= arrival_interval and i < departure_interval:
                    # The EV is connecteds
                    assert (value >= self.evpmin-0.001)	# At any given time, you need to keep the power draw at at least the minimum power
                    assert (value <= self.evpmax+0.001)	# At any given time, you need to keep the power draw at at most the maximum power
                
                else:
                    assert(value == 0)				# If the EV is gone you cannot charge it! Apparently you try to charge it.

                # Ensure the SoC is full upon departure
                if i == departure_interval:
                    assert(soc >= capacity-0.001)	# The EV must be fully charged upon departure. Are you charging enough power?

                soc += value
                assert (soc >= -0.001)				# The EV SoC must stay above 0. Are you charging enough?
                assert (soc <= capacity+0.001)		# THe EV SoC must stay below the SoC. Are you charging too much?


            # -- Verification without trips
            else:
                if i >= arrival_interval and i < departure_interval:
                    # The EV is connecteds
                    assert (value >= self.evpmin-0.001)	# At any given time, you need to keep the power draw at at least the minimum power
                    assert (value <= self.evpmax+0.001)	# At any given time, you need to keep the power draw at at most the maximum power

                else:
                    assert(value == 0)

        return True



# Run all cases
print(' ')
print('#######################################################################################')
print('Performing EV simulation code validation')
print('#######################################################################################')
print(' ')
print('NOTE: This script validates the simulation code and not the optimization assignments')
print(' ')

for i in range(0, 15):
    idx = i%len(pmax)
    e = EV(pmax[idx], pmin[idx], cap[idx], soc[idx], i)

print('------------------------------------------------------------------------------')
print('-- EV test finished; no problems found                                      --')
print('------------------------------------------------------------------------------')


