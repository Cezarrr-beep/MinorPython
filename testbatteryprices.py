import sys
import os
import copy
import time


sys.path.insert(1, os.path.join(sys.path[0], '..'))

from settings.constants import *
from helpers.helpers import *

# external classes
from battery.batterysim import *
from battery.batteryprices import *

import math
import random

tau = cfg_sim['tau']




def space(p, battery, soc, tau, i, j):
    u = battery.batcapacity - max(soc[i:j]) # Capacity for charging
    l = min(soc[i:j]) - battery.batminsoc # Capacity for discharging
    return (min(battery.batpmax - p[i], u/tau, p[j] - battery.batpmin), -min(p[i] - battery.batpmin, l/tau, battery.batpmax - p[j]))

def verifybatteryprices(battery, prices, planning):
    s=0
    soc=[s := s + tau*p for p in planning]

    for i in range(len(prices)):
        for j in range(i+1,len(prices)):
            (u,l) = space(planning, battery, soc, tau, i, j)
            if prices[i] < prices[j]:
                msg = f'Not optimal: increasing the charging power in interval {i} and decreasing it in interval {j} would decrease the costs'
                assert u < 0.001, msg
            elif prices[i] > prices[j]:
                msg = f'Not optimal: decreasing the charging power in interval {i} and increasing it in interval {j} would decrease the costs'
                assert l > -0.001, msg


    for i in range(len(prices)):
        if prices[i] < 0 and planning[i] < battery.batpmax:
            msg = f'Interval {i} has a negative price ({prices[i]}); a higher charging power reduces the costs (increase by {battery.batpmax - planning[i]})'
            assert battery.batcapacity - max(soc[i:]) <= 0.001,  msg
        elif prices[i] > 0 and planning[i] > battery.batpmin:
            msg = f'Interval {i} has a positive price ({prices[i]}); a lower charging power reduces the costs (decrease by {planning[i] - battery.batpmin})'
            assert min(soc[i:]) - battery.batminsoc >= -0.001, msg

################################################################################

# Test cases
pmax   = [ 1000,  1000,  1000,  1000,  100,    0,    0,  300,  100000]
pmin   = [-1000, -1000, -1000, -1000, -1000,    0, -100,    0, -100000]
bcap   = [    3,     3,     0,     3,    3,    3,    3,  0.5,     100]
soc    = [    0,   1.5,     0,     1,    0,    0,    2,  0.5,       0]
minsoc = [    0,     1,     0,     1,    0,    0,    2,  0.1,       0]


class Battery:
    def __init__(self, pmin, pmax, bcap, minsoc, soc):
        self.batsoc = soc
        self.batminsoc = minsoc
        self.batcapacity = bcap
        self.batpmin = pmin
        self.batpmax = pmax

        print(' ')
        print('------------------------------------------------------------------------------')
        print('-  Battery parameters: pmin='+str(pmin)+', pmax='+str(pmax)+', soc='+str(soc)+', minsoc='+str(minsoc)+', capacity='+str(bcap))
        print('------------------------------------------------------------------------------')

battery = Battery(-2000, 2000, 3, 0, 0)
target = battery.batcapacity


start = time.time()

n = 100 #cfg_sim['intervals']
prices = [10, 10, 10, 10, -20, -20, -20, -20, 30, 30, 30, 30, 20, 20, 20, 20, -10, -10, -10, -10, -15, -15, -15, -15]
co2 = [0] * n
baseprofile = [0] * n

random.seed(42)

# Run all cases
print(' ')
print('#######################################################################################')
print('Performing Battery price optimization code validation (FOR BONUS ONLY)')
print('#######################################################################################')
print(' ')

for i in range(0, len(pmax)):
    b = Battery(pmin[i], pmax[i], bcap[i], minsoc[i], soc[i])
    for j in range(78):
        print('*', end='', flush=True)
        prices = [random.randint(-10,10)*10 for p in [0] * n]
        planning = batteryprices(battery, prices, co2, baseprofile)
        
        verifybatteryprices(battery, prices, planning)
    print('')
print('')
end = time.time()
seconds = end - start


print( '------------------------------------------------------------------------------')
print(f'-- Battery test finished in {seconds:3.1f} seconds   ; no problems found               --')
print( '------------------------------------------------------------------------------')
