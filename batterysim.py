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
def batterysim(battery, planning):
    # FIXME: This is a placeholder that needs to be implemented

    # result parameter:
    profile = []

    # preparing local usage variables for the battery state:
    batsoc = battery.batsoc        
    batminsoc = battery.batminsoc    
    batcapacity = battery.batcapacity   
    batpmin = battery.batpmin       
    batpmax = battery.batpmax    
    tau = cfg_sim['tau']  

    for k in range(len(planning)):
        # Calculate the power to be drawn from or supplied to the battery
        p = planning[k]
        #Correct the ifs
        if p > batpmax:
            p = batpmax
        elif p < batpmin:
            p = batpmin

            #Calculate the Soc from this power
        new_soc= batsoc + (p * tau)

        if new_soc > batcapacity:
            p = (batcapacity - batsoc) / tau
            new_soc = batcapacity
        elif new_soc < batminsoc:
            p = (batminsoc - batsoc) / tau
            new_soc = batminsoc

        batsoc= new_soc    


        profile.append(p)
      
  

    # NOTE: The following variables help in the implementation of the code
    # NOTE: TREAT THESE VARIABLES AS READ-ONLY!
    
    # Battery parameters and variables are defined as follows:
    # batsoc        # State of Charge in kWh
    # batminsoc     # Minimum State of Charge in kWh
    # batcapacity   # Capacity of the battery in kWh
    # batpmin       # Minimum power in W (Negative value)
    # batpmax       # Maximum power in W

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

    # NOTE: The given code does not include the state of charge (SoC) of the battery
    # For this assignment you will need to implement SoC bookkeeping yourself and ensure that it stays within capacity bounds 

    # You can loop through the planning that is provided using e.g.,
    # for i in range(0, len(planning)):
    # Note that this for-statement would essentially step through the profile as if it were a discrete time simulation

    # Also, you could print(planning) to see what it looks like.



    # Returning the result
    return profile
