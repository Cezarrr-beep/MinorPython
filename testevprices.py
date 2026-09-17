import sys
import os
import copy


sys.path.insert(1, os.path.join(sys.path[0], '..'))

from settings.constants import *
from helpers.helpers import *

# external classes
from ev.evsim import *
from ev.evprices import *

import math
import random

def checktrip(ev, profile):
    capacity = 1000 * (3600 / cfg_sim['timebase']) * ev.evcapacity
    soc = 1000 * (3600 / cfg_sim['timebase']) * ev.evsoc
    minsoc = 1000 * (3600 / cfg_sim['timebase']) * ev.evminsoc
    intervals_per_day = (3600 / cfg_sim['timebase']) * 24
    intervals_per_hour = (3600 / cfg_sim['timebase'])

    for i in range(0, len(profile)):
        # check availability:
        arrival_day = math.floor(i / intervals_per_day)
        arrival_interval = int(arrival_day * intervals_per_day + ev.evarrivalhour * intervals_per_hour)
        departure_interval = int(arrival_interval + ev.evconnectiontime * intervals_per_hour)

        value = profile[i]

        if i == arrival_interval:
            soc -= ev.evenergy * 1000 * (3600 / cfg_sim['timebase'])
            assert soc >= -0.001, 'soc is negative'    # The EV SoC must be always positive. Your simulation code resulted in a negative SoC. Are you charging enough power?
        soc += value
        
        # Ensure the SoC is full upon departure
        if i == departure_interval:
            assert soc >= capacity-0.001, 'EV not fully charged'	# The EV must be fully charged upon departure. Are you charging enough power?

        assert soc >= -0.001, 'EV is discharging'		        # The EV SoC must stay above 0. Are you charging enough?
        assert soc <= capacity+0.001, 'EV SoC exceeds battery capacity'		# The EV SoC must stay below the capacity. Are you charging too much?

def checkcharging(ev, planning, prices, days=None):
    intervals_per_day = (3600 / cfg_sim['timebase']) * 24
    intervals_per_hour = (3600 / cfg_sim['timebase'])

    if days == None:
        days = math.floor(len(profile) / intervals_per_day)

    for arrival_day in range(days):
        arrival_interval = int(arrival_day * intervals_per_day + ev.evarrivalhour * intervals_per_hour)
        departure_interval = int(arrival_interval + ev.evconnectiontime * intervals_per_hour)

        for i in range(arrival_interval, departure_interval):
            for j in range(arrival_interval, departure_interval):
                if (prices[i] > prices[j]):
                    assert planning[i] <= planning[j], f'prices[{i}]={prices[i]} > prices[{j}]={prices[j]}, but planning[{i}]={planning[i]} > planning[{j}]={planning[j]} (not optimal). prices={prices}.' # Check if we do not charge when another interval is cheaper
    

pmax   = [ 1000,  1000,   4000];
pmin   = [    0,     0,      0];
cap    = [   30,    20,     70];
soc    = [    0,   1.5,      6];

class EV:
    pass


# First start with some static tests to find common mistakes
ev = EV()
ev.evpmax = 1250;
ev.evpmin = 0;
ev.evcapacity = 50
ev.evsoc = ev.evcapacity
ev.evenergy = 2
ev.evminsoc = ev.evenergy
ev.evconnectiontime = ev.evenergy+2
ev.evarrivalhour = 2

print(' ')
print('------------------------------------------------------------------------------')
print('-- Check boundary cases                                                     --')
print('------------------------------------------------------------------------------')
print(' ')

print('* Checking constant prices')
prices = [1000]*30
profile = [0] * 30
planning = evprices(copy.deepcopy(ev), copy.deepcopy(prices), copy.deepcopy(prices), profile)
evplanning = evsim(copy.deepcopy(ev), copy.deepcopy(planning))
checktrip(ev, evplanning)
checkcharging(ev, evplanning, prices)

print('* Checking increasing prices')
prices = list(range(30))
profile = [0] * 30
planning = evprices(copy.deepcopy(ev), copy.deepcopy(prices), copy.deepcopy(prices), profile)
evplanning = evsim(copy.deepcopy(ev), copy.deepcopy(planning))
checktrip(ev, evplanning)
checkcharging(ev, evplanning, prices, 1)

# Fail if evsim or evprices change the list of prices.
print('* Check if prices are altered')
assert prices == list(range(30)), 'evsim or evprices changed the prices'

print('* Checking decreasing prices')
prices = prices[::-1]
planning = evprices(copy.deepcopy(ev), copy.deepcopy(prices), copy.deepcopy(prices), profile)
evplanning = evsim(copy.deepcopy(ev), copy.deepcopy(planning))
checktrip(ev, evplanning)
checkcharging(ev, evplanning, prices, 1)

# The function 'evprices' should not use the profile to determine where to charge the EV.
print('* Checking if profile is used incorrectly')
profile = [ -p for p in prices] # PV generation when the price is high: we should not charge!
planning = evprices(copy.deepcopy(ev), copy.deepcopy(prices), copy.deepcopy(prices), profile)
evplanning = evsim(copy.deepcopy(ev), copy.deepcopy(planning))
checktrip(ev, evplanning)
checkcharging(ev, evplanning, prices, 1)

# If a price occurs multiple times, a treshold based approach might not work. You can fix this by adding a tiny unique value to each price (note: work with a copied list!)
print('* Checking if duplicated prices cause problems')
indexlow = int((3600 / cfg_sim['timebase']) * ev.evconnectiontime + 1) # One interval has a low price, others are constant
prices = [1000]*30
prices[indexlow] = 100
prices[indexlow+7] = 100
planning = evprices(copy.deepcopy(ev), copy.deepcopy(prices), copy.deepcopy(prices), profile)
evplanning = evsim(copy.deepcopy(ev), copy.deepcopy(planning))
checktrip(ev, evplanning)
checkcharging(ev, evplanning, prices, 1)


# Additional random testing with multiple departures
for i in range(0, 15):
    idx = i%len(pmax)


    # Static Charging session duration
    ev = EV()
    ev.evpmax = pmax[idx]
    ev.evpmin = pmin[idx]
    ev.evcapacity = cap[idx]
    ev.evsoc = ev.evcapacity
    ev.evenergy = 5+(idx%5)					# Energy demand in kWh per driving session
    ev.evminsoc =	ev.evenergy 				# Minimum SoC to reach after each session (because of driving)
    ev.evconnectiontime = ev.evenergy + 2 	# Hours the EV is connected
    ev.evarrivalhour = 12+(idx%7)				# Hour of arrival of the EV each day

    prices = [random.randint(-10,10)*10 for p in [0] * cfg_sim['intervals']]
    
    print(' ')
    print('------------------------------------------------------------------------------')
    print('-  EV parameters: pmin='+str(ev.evpmin)+', pmax='+str(ev.evpmax)+', soc='+str(ev.evsoc)+', minsoc='+str(ev.evminsoc)+', capacity='+str(ev.evcapacity))
    print('-  EV trip parameters: arrival='+str(ev.evarrivalhour)+':00, connected='+str(ev.evconnectiontime)+'h, driving session='+str(ev.evenergy)+'kWh')
    print('------------------------------------------------------------------------------')


    pricescopy = copy.deepcopy(prices)
    profile = [0] * cfg_sim['intervals']
    planning = evprices(copy.deepcopy(ev), pricescopy, copy.deepcopy(prices), profile)
    evplanning = evsim(copy.deepcopy(ev), copy.deepcopy(planning))

    assert pricescopy == prices, 'evsim or evprices changed the prices' # Check if evprices changed the prices...
    checktrip(ev, evplanning)
    checkcharging(ev, evplanning, prices)

print(' ')
print('##############################################################################')
print('#                                                                            #')
print('#    EV prices optimization test finished successfully                       #')
print('#                                                                            #')
print('##############################################################################')

