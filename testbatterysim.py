import sys
import os
import copy
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from settings.constants import *
from helpers.helpers import *

# external classes
from battery.batterysim import *

import math
import random
import copy

# Test cases
pmax   = [ 1000,  1000,  1000,  1000,  100,    0,    0,  300,  100000]
pmin   = [-1000, -1000, -1000, -1000, -1000,    0, -100,    0, -100000]
bcap   = [    3,     3,     0,     3,    3,    3,    3,  0.5,     100]
soc    = [    0,   1.5,     0,     1,    0,    0,    2,  0.5,       0]
minsoc = [    0,     1,     0,     1,    0,    0,    2,  0.1,       0]


class Battery():
    def __init__(self, pmax, pmin, bcap, soc, minsoc):
        self.batsoc = soc
        self.batminsoc = minsoc
        self.batcapacity = bcap
        self.batpmin = pmin
        self.batpmax = pmax

    def run_tests(self):
        print(' ')
        print('------------------------------------------------------------------------------')
        print('-  Battery parameters: pmin='+str(pmin)+', pmax='+str(pmax)+', soc='+str(soc)+', minsoc='+str(minsoc)+', capacity='+str(bcap))
        print('------------------------------------------------------------------------------')

  
        # Run all test cases
        # Test constant charging
        print('Testing constant charging')
        for p in [10,1000,2000,4000,8000,20000]:
            planning = [p] * 100
            self.execute(planning)

        # Test constant discharging
        print('Testing constant discharging')
        for p in [10,1000,2000,4000,8000,20000]:
            planning = [-p]*100
            self.execute(planning)

        # Charge and discharge cycles
        print('Testing periodic charging/discharging')
        for T in range(1,10):
            planning = []
            for i in range(0, cfg_sim['intervals'] ):
                planning.append(T*1000*math.sin(((i*T)/cfg_sim['intervals'])*2*math.pi))
            self.execute(planning)

        # Random charging
        print('Testing random profile; independent')
        for n in range(0, 20):
            planning = []
            for i in range(0, 1000):
                planning.append(1000 * random.random())
            self.execute(planning)

        # Random charging (with memory)
        print('Testing random profile; dependent')
        for n in range(0, 20):
            planning = []
            s = 0
            for i in range(0, 1000):
                planning.append(s + (100 * random.random()))
                s = planning[-1]
            self.execute(planning)

    def run_clipping(self):
        print(' ')
        print('------------------------------------------------------------------------------')
        print('-  Battery parameters: pmin='+str(pmin)+', pmax='+str(pmax)+', soc='+str(soc)+', minsoc='+str(minsoc)+', capacity='+str(bcap))
        print('------------------------------------------------------------------------------')

  
        # Specific clipping test
        print('Comparing output list with expected list')
        planning = [3000, 3000, 3000, 3000, 3000, 3000, 0, 0, -2000, -2000, -2000, -2000, -2000, -2000, -2000, -2000, -2000, -2000]
        expected = [1500, 1500, 1500,  500,    0,    0, 0, 0,  -750,  -750,  -750,  -750,  -750,  -750,  -750,  -250,     0,     0]
        result = self.execute(planning)

        assert(len(planning) == len(result) == len(expected))

        for i in range(0, len(result)):
            assert result[i] >= expected[i]-0.001, f'The resulting power from the battery is lower than expected'
            assert result[i] <= expected[i]+0.001, f'The resulting power from the battery is higher than expected'

        return True


    # Simulation code
    def execute(self, planning):
        # pre validation
        if not self.verify_input():
            print("The input parameters for device are invalid! Aborting! Most likely you have not added (enough) values to the profile list using profile.append(<value>).")
            exit()

        # Perform the simulation
        returnprofile = self.simulate(copy.deepcopy(planning))
        if not self.verify_result(returnprofile, planning):
            print("The simulation of device failed! Aborting! Most likely you are violating our constraints. Carefully read the error log above and the comments in the code that caused the crash.")
            exit()

        # Check if batterysim is idempotent: the output 'returnprofile' of batterysim was corrected, so running batterysim with this as input should have no effect.
        returnprofile2 = self.simulate(copy.deepcopy(returnprofile))
        mhdiff = sum([abs(x-y) for x,y in zip(returnprofile, returnprofile2)])/len(returnprofile)
        if mhdiff > 0.5:
            print("Calling batterysim on its own output results in a different profile (it 'fixes' a corrected profile).")
            #print(f"Original profile: {planning}, batterysim output: {returnprofile}, second output: {returnprofile2}") # uncomment this line if you'd like to debug this error.
            exit()
        return returnprofile


    # Simulation code
    def simulate(self, planning=[]):
        return batterysim(copy.deepcopy(self), copy.deepcopy(planning))

    # Function to verify the created planning by the optimization code
    # But also to verify user input, is it valid input?
    def verify_input(self):
        assert (self.batcapacity >= 0)
        assert (self.batminsoc >= 0)
        assert (self.batsoc >= 0)
        assert (self.batsoc <= self.batcapacity)
        assert (self.batminsoc <= self.batcapacity)
        assert (self.batpmin <= self.batpmax)

        return True


    # Function to verify if the code functions correctly
    def verify_result(self, profile, planning):
        # Internal conversion to Wtau
        capacity = 1000 * (3600 / cfg_sim['timebase']) * self.batcapacity
        soc = 1000 * (3600 / cfg_sim['timebase']) * self.batsoc
        minsoc = 1000 * (3600 / cfg_sim['timebase']) * self.batminsoc

        assert (len(profile) == len(planning))
        for value in profile:
            assert (value >= self.batpmin-0.001)	# The power drawn must be at least the minimum power (maximal discharging)
            assert (value <= self.batpmax+0.001)	# The power drawn must be at most the maximum power (maximal charging)

            # determine if the SoC at the end of the interval will be in bounds
            soc += value

            assert (soc >= minsoc - 0.1)	# The SoC must remain positive. Are you discharging too much?
            assert (soc <= capacity + 0.1)	# The SoC cannot be higher than the capacity. Are you charging too much?


        # Now check if the battery did something useful in terms of power
        # We do not expect a zero power profile in many cases. However, we also do not an extensive test
        sum_profile = sum(map(abs, profile))
        sum_planning = sum(map(abs, planning))

        if sum_planning > 0 and self.batcapacity > 0 and self.batsoc != self.batminsoc and self.batsoc != self.batcapacity and self.batpmin != 0 and self.batpmax != 0:
            assert (sum_profile > 0)        # The battery should at least do something and not just return a profile of zeroes

        for i in range(0, len(profile)):
            if planning[i] > 0:
                assert(profile[i] >= -0.001)    # The battery should definitely not discharge if the planning is positive
            elif planning[i] < 0:
                assert(profile[i] <= 0.001)    # The battery should definitely not charge if the planning is negative

        return True




# Run all cases
print(' ')
print('#######################################################################################')
print('Performing Battery simulation code validation')
print('#######################################################################################')
print(' ')
print('NOTE: This script validates the simulation code and not the optimization assignments')
print(' ')

for i in range(0, len(pmax)):
    b = Battery(pmax[i], pmin[i], bcap[i], soc[i], minsoc[i])
    b.run_tests()

# Specific clipping test
b = Battery(1500, -750, 1.5, 0.25, 0.125)
b.run_clipping()

print('------------------------------------------------------------------------------')
print('-- Battery test finished; no problems found                                 --')
print('------------------------------------------------------------------------------')
