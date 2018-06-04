#!/bin/bash
# Script for running tests and generating graphs.

# Clear previous perm_output 
<<<<<<< HEAD
sudo rm -rf perm_output
mkdir perm_output
=======
cd perm_output
sudo rm *
cd ..
>>>>>>> 90809083a945c9c2acde807930253ac2b1f3bc3c

# Make sure mininet state is clean and that no other process is running on port 6633.
sudo mn -c

# Run experiments for graphs 10a,c.
<<<<<<< HEAD
sudo python experiment.py ftree ecmp active-servers 10 5
sudo python experiment.py xpander ecmp active-servers 10 5
sudo python experiment.py xpander hyb active-servers 10 5
=======
sudo python experiment.py ftree ecmp active-servers 10
sudo python experiment.py xpander ecmp active-servers 10
sudo python experiment.py xpander hyb active-servers 10
>>>>>>> 90809083a945c9c2acde807930253ac2b1f3bc3c

# Generate graph 10a
python analysis.py 10a

# Generate graph 10c
python analysis.py 10c

# Run experiments for graphs 11a,c.
<<<<<<< HEAD
# sudo python experiment.py ftree ecmp lambda 10 1
# sudo python experiment.py xpander ecmp lambda 10 1
# sudo python experiment.py xpander hyb lambda 10 1
=======
# sudo python experiment.py ftree ecmp lambda 10
# sudo python experiment.py xpander ecmp lambda 10
# sudo python experiment.py xpander hyb lambda 10
>>>>>>> 90809083a945c9c2acde807930253ac2b1f3bc3c

# Generate graph 11a
# python analysis.py 11a

# Generate graph 11c
# python analysis.py 11c
