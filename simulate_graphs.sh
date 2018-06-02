#!/bin/bash
# Script for running tests and generating graphs.

# Clear previous perm_output 
cd perm_output
sudo rm *
cd ..

# Make sure mininet state is clean and that no other process is running on port 6633.
sudo mn -c

# Run experiments for graphs 10.
sudo python experiment.py ftree ecmp active-servers 10
sudo python experiment.py xpander ecmp active-servers 10
sudo python experiment.py xpander hyb active-servers 10

# GENERATE GRAPH 10(A)
python analysis.py 10a

# GENERATE GRAPH 10(C)
python analysis.py 10c

# Run experiments for graphs 10.
sudo python experiment.py ftree ecmp lambda 10
sudo python experiment.py xpander ecmp lambda 10
sudo python experiment.py xpander hyb lambda 10

# GENERATE GRAPH 11(A)
python analysis.py 11a

# GENERATE GRAPH 11(C)
python analysis.py 11c