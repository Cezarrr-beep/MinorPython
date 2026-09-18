from settings.constants import *

# Check if the script is not executed directly, but called through simulator or a test script
import sys
import os
if os.path.basename(sys.argv[0]) != 'simulator.py' and os.path.basename(sys.argv[0])[:4] != 'test':
    print("ERROR: You cannot directly execute this file, but need to execute simulator.py or a test script")
    quit()
    
import math
import random

# This function simulates the behaviour of the device

# Function arguments:
#
# Input:
#   - ev:       Object representing the data structure of EV properties (see comments below)
#   - planning: A vector (list) representing the planned power values per interval in Watts
#
#
# Returns:
#   - profile: A vector (list) representing the actual power consumption per interval (per your implemented algorithm) in Watts
#
# Notes: 
#   - the length of profile (i.e., number of elements) must equal the lenghth of the planning list (input)
#   - With default settings this is 672 elements (7 days times 96 intervals (of 15 mins) per day)
#   - Do not change the function definition on the next line
def evsim(ev, planning):
    # result parameter:
    profile = []

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
  

    # NOTE: The following variables help in the implementation of the code
    # NOTE: TREAT THESE VARIABLES AS READ-ONLY!
    
    # ev parameters and variables are defined as follows:
    # evsoc              # State of Charge of the EV in kWh
    # evminsoc           # Minimum State of Charge of the EV in kWh (because of driving)
    # evcapacity         # Capacity of the EV in kWh
    # evpmin             # Minimum power of the EV in W = 0 W (EV cannot discharge. No V2G is possible.)
    # evpmax             # Maximum power of the EV in W
    # evenergy           # Energy consumption of the EV over one driving session in kWh

    # Timing variables are defined as follows:
    # evconnectiontime   # Hours the EV is connected
    # evarrivalhour      # Hour of arrival of the EV each day

    # Other input
    # The profile vector provides values in Watt for each discrete interval (to be complete, this is the average power consumption in W during an interval)
    # Negative values indicate overproduction.



    # Running the simulation of the device

    # Your task is to modify the code such that the list containing the resulting power profile is filled (this is the simulation outcome). 
    # This is also a list, with each value representing the power consumption (average) during an interval in Watts
    # The length of this list must be equal to the input vectors (i.e., planning)

    # For each interval i, these can be set by adding the correction value to the planning list, i.e.:
    # profile.append(<your_value>)
    # NOTE: Make sure that at the end the number of elements in profile equals the (original) length of the planning vector

    # NOTE: The given code does not include that the state of charge (SoC) of the EV battery is reduced due to driving
    # For this assignment you will need to implement SoC bookkeeping yourself and ensure that it stays within capacity bounds 
    # Tip: Use the "evenergy" variable for this in your code

    # What is already given is to determine if the EV is connected to the charging station (at home) or not (driving)
    intervals_per_day = (3600 / cfg_sim['timebase']) * 24
    intervals_per_hour = (3600 / cfg_sim['timebase'])

    # Looping through the provided planning vector
    for i in range(0, len(planning)):
        # Note that this for-statement would essentially step through the profile as if it were a discrete time simulation
        # check availability:
        arrival_day = math.floor(i/intervals_per_day)
        arrival_interval = int(arrival_day*intervals_per_day + ev.evarrivalhour * intervals_per_hour)
        departure_interval = int(arrival_interval + ev.evconnectiontime * intervals_per_hour)

        # Check for overruns:
        if ev.evarrivalhour+ev.evconnectiontime >= 24:
            if departure_interval - (24 * (3600 / cfg_sim['timebase'])) >= i and arrival_interval - (24 * (3600 / cfg_sim['timebase'])) > 0:
                departure_interval -= int(24 * (3600 / cfg_sim['timebase']))
                arrival_interval -= int(24 * (3600 / cfg_sim['timebase']))

        # FIXME Here you will need to implement the behaviour of the electric vehicle
        # You do not necessarily need to use all if-constructs, but they are defined for your convenience if you wish to make use of them
        # Keep the "pass" if you do not want to use one of the if-constructs.

        # NOTE: You will need to do two things:
        # 1. Update the SoC of the EV at the right time (see Lecture 2) by deducting the energy of a driving session
        # 2. Create the code to optimize the power profile of the EV
        
        
        #Differences: EV can only charge while it is connectd
        # Every time it arrives, the evsoc is reduced by the evenergy.




        if i == arrival_interval:
            # Moment at which the EV arrives
            evsoc -= evenergy
            

        if i >= arrival_interval and i < departure_interval:
            # Interval that the EV is connected (available)
        
            p=planning[i]

            #Cannot discharge the ev
            if p< evpmin:
                p=evpmin
                #if it is bigger that the max power.
            elif p>evpmax:
                p=evpmax
            new_soc= evsoc + p*tau  #new_soc definition.
                #make sure that soc is not bigger that te capacity of the ev.
            if new_soc > evcapacity:
                p  = (evcapacity - evsoc)/tau
                new_soc=evcapacity

            evsoc=new_soc
            

        else:
            # Interval that the EV is disconnected (unavailable) even though it is in the time inerval.
            p=0

        profile.append(p)


    # Finally, the resulting power profile for the device must be returned
    return profile
