#!/bin/bash
# Script for running tests and generating graphs.

# GENERATE GRAPH 10(A)

# GENERATE GRAPH 10(C)
sudo python experiment.py ftree ecmp active-servers 10
python analysis.py 10c

# SIMULATE EXPERIMENTS FOR 11a and 11c
sudo python experiment.py ftree ecmp lambda 10
sudo python experiment.py xpander ecmp lambda 10
sudo python experiment.py xpander hyb lambda 10

# GENERATE GRAPH 11(A)
python analysis.py 11a

# GENERATE GRAPH 11(C)
python analysis.py 11c
