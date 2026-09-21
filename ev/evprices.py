from settings.constants import *

# Check if the script is not executed directly, but called through simulator or a test script
import sys
import os
if os.path.basename(sys.argv[0]) != 'simulator.py' and os.path.basename(sys.argv[0])[:4] != 'test':
    print("ERROR: You cannot directly execute this file, but need to execute simulator.py or a test script")
    quit()

    
import math
import random

# With this function, a planning for the operation (i.e. control actions) can be implemented

# Function arguments:
#
# Input:
#   - ev:       Object representing the data structure of EV properties (see comments below)
#   - prices:   A vector (list) representing the electricity price per interval (element)
#   - co2:      A vector (list) representing the CO2 emissions from the national energy mix per interval (element)
#   - profile:  A vector (list) representing the aggregated load and generation of other devices in the house per interval. This is: base load, PV and wind generation
#
# Returns:
#   - planning: A vector (list) representing the planned power values per interval (per your implemented algorithm) in Watts
#
# Notes: 
#   - the length of planning (i.e., number of elements) must equal the lenghth of the profile list (input)
#   - use the input arguments as read only!
#   - assume len(prices) == len(co2) == len(profile) 
#   - With default settings this is 672 elements (7 days times 96 intervals (of 15 mins) per day)
#   - Do not change the function definition on the next line
def evprices(ev, prices, co2, profile):
    # result parameter to be filled and returned in the end:
    # Initialize to all zeros: 0 W is the correct default for every interval
    # where the EV isn't connected, or connected but not chosen for charging.
    planning = [0] * len(profile)

    # preparing local usage variables for the EV state:
    evsoc = ev.evsoc
    evminsoc = ev.evminsoc
    evcapacity = ev.evcapacity
    evpmin = ev.evpmin
    evpmax = ev.evpmax
    evenergy = ev.evenergy
    evarrivalhour = ev.evarrivalhour
    evconnectiontime = ev.evconnectiontime
    tau = cfg_sim['tau']

    intervals_per_day = (3600 / cfg_sim['timebase']) * 24
    intervals_per_hour = (3600 / cfg_sim['timebase'])

    # Running SoC, used only for bookkeeping across days as the loop progresses
    soc = evsoc

    for i in range(0, len(profile)):
        arrival_day = math.floor(i / intervals_per_day)
        arrival_interval = int(arrival_day * intervals_per_day + ev.evarrivalhour * intervals_per_hour)
        departure_interval = int(arrival_interval + ev.evconnectiontime * intervals_per_hour)

        if ev.evarrivalhour + ev.evconnectiontime >= 24:
            if departure_interval - (24 * (3600 / cfg_sim['timebase'])) >= i and arrival_interval - (24 * (3600 / cfg_sim['timebase'])) > 0:
                departure_interval -= int(24 * (3600 / cfg_sim['timebase']))
                arrival_interval -= int(24 * (3600 / cfg_sim['timebase']))

        if i == arrival_interval:
            # 1. Deduct the energy used getting here (SoC bookkeeping, per Lecture 2)
            soc -= evenergy
            if soc < evminsoc:
                soc = evminsoc  # safety clip; shouldn't trigger for a feasible scenario

            # 2. How much energy is still needed to reach a full battery by departure?
            energy_needed = evcapacity - soc

            # 3. Clip this session to the simulated horizon (start/end-of-week edges)
            session_start = max(arrival_interval, 0)
            session_end = min(departure_interval, len(profile))
            session_length = session_end - session_start

            if session_length > 0 and energy_needed > 0:
                # 4. Rank this session's intervals by price, cheapest first
                session_prices = prices[session_start:session_end]
                order = sorted(range(session_length), key=lambda k: session_prices[k])

                # 5. Fill the cheapest intervals at max power first, until fully charged
                remaining_energy = energy_needed
                for idx in order:
                    if remaining_energy <= 0:
                        break
                    interval_energy = tau * evpmax  # kWh deliverable at full power this interval
                    if interval_energy <= remaining_energy:
                        planning[session_start + idx] = evpmax
                        remaining_energy -= interval_energy
                    else:
                        # Last interval needed: charge just enough to finish exactly
                        planning[session_start + idx] = remaining_energy / tau
                        remaining_energy = 0

            # The plan guarantees the EV is full by departure
            soc = evcapacity

        if i >= arrival_interval and i < departure_interval:
            # Connected: handled above at arrival, nothing further needed per-interval
            pass
        else:
            # Disconnected: planning already defaults to 0 here
            pass

        if i == departure_interval:
            pass

    return planning