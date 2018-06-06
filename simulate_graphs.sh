#!/bin/bash
# Script for running tests and generating graphs.

# Clear previous perm_output 
sudo rm -rf perm_output
mkdir perm_output

# Make sure mininet state is clean and that no other process is running on port 6633.
sudo mn -c

# # Run experiments for graphs 10a,c.
sudo python experiment.py ftree ecmp both 10 10
sudo python experiment.py xpander ecmp both 10 10
sudo python experiment.py xpander hyb both 10 10

# Generate graph 10a
python analysis.py 10a

# Generate graph 10c
python analysis.py 10c

# Run experiments for graphs 11a,c.
sudo python experiment.py ftree ecmp lambda 10
sudo python experiment.py xpander ecmp lambda 10
sudo python experiment.py xpander hyb lambda 10

# Generate graph 11a
python analysis.py 11a

# Generate graph 11c
python analysis.py 11c
