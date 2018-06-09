#!/bin/bash
# Script for running tests and generating graphs.

# Clear previous perm_output 
sudo rm -rf perm_output
mkdir perm_output

# Make sure mininet state is clean and that no other process is running on port 6633.
sudo mn -c

# # Run experiments for graphs 10a,c.
sudo python experiment.py ftree ecmp active-servers 10 10
sudo python experiment.py xpander ecmp active-servers 10 10
sudo python experiment.py xpander hyb active-servers 10 10

# Generate graph 10a
python analysis.py 10a

# Generate graph 10c
python analysis.py 10c

# Run experiments for graphs 11a,c.
sudo python experiment.py ftree ecmp lambda 10 10
sudo python experiment.py xpander ecmp lambda 10 10
sudo python experiment.py xpander hyb lambda 10 10

# Generate graph 11a
python analysis.py 11a

# Generate graph 11c
python analysis.py 11c

# Remove previous logs
sudo rm -f ftree_ecmp.log
sudo rm -f xpander_ecmp.log
sudo rm -f xpander_hyb.log

# Run custom experiments and save controller logs to generate switchloads.png and pathlengths.png
sudo python experiment.py ftree ecmp custom 1 1
mv ../../custom_controller.log ftree_ecmp.log
sudo python experiment.py xpander ecmp custom 1 1
mv ../../custom_controller.log xpander_ecmp.log
sudo python experiment.py xpander hyb custom 1 1
mv ../../custom_controller.log xpander_hyb.log

# Generate graph of path lengths and switch loads
sudo python pathlengths.py
sudo python switchloads.py
