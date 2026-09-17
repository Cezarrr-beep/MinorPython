import sys
import os
import copy


sys.path.insert(1, os.path.join(sys.path[0], '..'))

from settings.constants import *
from helpers.helpers import *

# external classes
from ev.evsim import *
from ev.evself import *

import math
import random

tau = cfg_sim['tau']


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

def checkcharging(ev, planning, profile, days=None):
    intervals_per_day = (3600 / cfg_sim['timebase']) * 24
    intervals_per_hour = (3600 / cfg_sim['timebase'])

    if days == None:
        days = math.floor(len(profile) / intervals_per_day)

    for arrival_day in range(days):
        arrival_interval = int(arrival_day * intervals_per_day + ev.evarrivalhour * intervals_per_hour)
        departure_interval = int(arrival_interval + ev.evconnectiontime * intervals_per_hour)

        surplus = 0
        selfconsumption = 0
        for i in range(arrival_interval, departure_interval):
            if (profile[i] < 0):
                surplus = surplus + tau*min(-profile[i], ev.evpmax)
                selfconsumption = selfconsumption + tau*min(-profile[i], planning[i])
        chargable_surplus = min(surplus, ev.evenergy) # Expected self consumption: the EV charging amount limited by the surplus.

        # The charged surplus should be equal to the chargable surplus. 
        assert abs(chargable_surplus - selfconsumption) < 0.001, f'On day {1+arrival_day} less energy was charged from surplus renewable energy than possible: chargable surplus={chargable_surplus}, charged surplus={selfconsumption}.'
        #print(f'To charge={ev.evenergy}, Chargable surplus={expself}, charged surplus={selfconsumption}')

pmax   = [ 1000,  1000,   4000];
pmin   = [    0,     0,      0];
cap    = [   30,    20,     70];
soc    = [    0,   1.5,      6];

class EV:
    pass


# First start with some static tests to find common mistakes
ev = EV()
ev.evpmax = 1000;
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

print('* Checking constant load')
prices = [0] * 30
profile = [1000] * 30
planning = evself(copy.deepcopy(ev), copy.deepcopy(prices), copy.deepcopy(prices), profile)
evplanning = evsim(copy.deepcopy(ev), copy.deepcopy(planning))
checktrip(ev, evplanning)
checkcharging(ev, evplanning, profile)

print('* Checking increasing load')
profile = list(range(-15,15))
planning = evself(copy.deepcopy(ev), copy.deepcopy(prices), copy.deepcopy(prices), profile)
evplanning = evsim(copy.deepcopy(ev), copy.deepcopy(planning))
checktrip(ev, evplanning)
checkcharging(ev, evplanning, profile, 1)

# Fail if evsim or evself change the list of loads.
print('* Check if loads are altered')
assert profile == list(range(-15,15)), 'evsim or evself changed the loads'

print('* Checking decreasing loads')
profile = profile[::-1]
planning = evself(copy.deepcopy(ev), copy.deepcopy(prices), copy.deepcopy(prices), profile)
evplanning = evsim(copy.deepcopy(ev), copy.deepcopy(planning))
checktrip(ev, evplanning)
checkcharging(ev, evplanning, profile, 1)

# The function 'evself' should not use the prices to determine where to charge the EV.
print('* Checking if prices is used incorrectly (should not influence the profile)')
prices = [ -p for p in profile] # low price when PV is low: we should not charge!
planning = evself(copy.deepcopy(ev), copy.deepcopy(prices), copy.deepcopy(prices), profile)
evplanning = evsim(copy.deepcopy(ev), copy.deepcopy(planning))
checktrip(ev, evplanning)
checkcharging(ev, evplanning, profile, 1)

# The function 'evself' should not use the CO2 to determine where to charge the EV.
print('* Checking if prices is used incorrectly (should not influence the profile)')
prices = [0] * 30
co2 = [ -p for p in profile] # low CO2 when PV is low: we should not charge!
planning = evself(copy.deepcopy(ev), copy.deepcopy(prices), copy.deepcopy(co2), profile)
evplanning = evsim(copy.deepcopy(ev), copy.deepcopy(planning))
checktrip(ev, evplanning)
checkcharging(ev, evplanning, profile, 1)

# If a level occurs multiple times, a treshold based approach might not work.
print('* Checking if duplicated loads cause problems')
indexlow = int((3600 / cfg_sim['timebase']) * ev.evconnectiontime + 1) # One interval has generation, others are constant
profile = [1000]*30
profile[indexlow] = -100
profile[indexlow+7] = -100
planning = evself(copy.deepcopy(ev), copy.deepcopy(prices), copy.deepcopy(prices), profile)
evplanning = evsim(copy.deepcopy(ev), copy.deepcopy(planning))
checktrip(ev, evplanning)
checkcharging(ev, evplanning, profile, 1)


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
    ev.evminsoc = ev.evenergy                                   # Minimum SoC to reach after each session (because of driving)
    ev.evconnectiontime = ev.evenergy + 2                       # Hours the EV is connected
    ev.evarrivalhour = 12+(idx%7)				# Hour of arrival of the EV each day

    profile = [random.randint(-1000,1000)*10 for p in [0] * cfg_sim['intervals']]
    
    print(' ')
    print('------------------------------------------------------------------------------')
    print('-  EV parameters: pmin='+str(ev.evpmin)+', pmax='+str(ev.evpmax)+', soc='+str(ev.evsoc)+', minsoc='+str(ev.evminsoc)+', capacity='+str(ev.evcapacity))
    print('-  EV trip parameters: arrival='+str(ev.evarrivalhour)+':00, connected='+str(ev.evconnectiontime)+'h, driving session='+str(ev.evenergy)+'kWh')
    print('------------------------------------------------------------------------------')


    prices = [random.randint(-1000,1000)*10 for p in [0] * cfg_sim['intervals']] # should not influence the results
    co2 = [random.randint(-1000,1000)*10 for p in [0] * cfg_sim['intervals']] # should not influence the results
    pricescopy = copy.deepcopy(prices)
    co2copy = copy.deepcopy(co2)
    profilecopy = copy.deepcopy(profile)
    planning = evself(copy.deepcopy(ev), pricescopy, co2copy, profile)
    evplanning = evsim(copy.deepcopy(ev), copy.deepcopy(planning))

    assert pricescopy == prices, 'evsim or evself changed the prices' # Check if evself changed the prices...
    assert profilecopy == profile, 'evsim or evself changed the profile' # Check if evself changed the profile...
    assert co2copy == co2, 'evsim or evself changed the CO2' # Check if evself changed the CO2...
    checktrip(ev, evplanning)
    checkcharging(ev, evplanning, profile)

print(' ')
print('##############################################################################')
print('#                                                                            #')
print('#    EV self-consumption optimization test finished successfully             #')
print('#                                                                            #')
print('##############################################################################')

