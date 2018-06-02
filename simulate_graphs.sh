#!/bin/bash
# Script for running tests and generating graphs.

# GENERATE GRAPH 10(A)

# GENERATE GRAPH 10(C)
sudo python experiment.py ftree ecmp active-servers 10
python analysis.py 10c

# GENERATE GRAPH 11(A)

# GENERATE GRAPH 11(C)