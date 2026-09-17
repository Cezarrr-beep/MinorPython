#!/usr/bin/python3

import sys
import os

# get the path to the folder named "python"
pythonFolderDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# insert the path to the folder named "python" into the system path
sys.path.insert(1, pythonFolderDir)
p = sys.path[0]

# change the directory to the folder named "python"
os.chdir(pythonFolderDir)

sys.argv = ['simulator.py', 'validation']
from simulator import *

# change back the directory
os.chdir(p)

input("Press Enter to exit.")