import json
import itertools
import re
import matplotlib.pyplot as plt
import csv
import re
from collections import defaultdict
import sys
import os
import math

debug = None
DATA_DIR = "perm_output/"


def readThroughputFromCSV(arr, filename):
  # CSV headers:
  # 0 = timestamp
  # 1 = source_address
  # 2 = source_port
  # 3 = destination_address
  # 4 = destination_port
  # 5 = interval
  # 6 = transferred_bytes
  # 7 = bits_per_second      
  with open(DATA_DIR+filename, 'rb') as f:
    reader = csv.reader(f)
    for row in reader:
      arr.append(int(row[7]))
    f.close()

def computeAllThroughputAvgs(avg_dict):
  for (key, value) in avg_dict.iteritems():
    observation_len = len(value)
    avg_dict[key] = sum(value) / len(value)
    avg_dict[key] /= math.pow(10, 9) # Divide by 10^9 to get gigabytes

def generate10c():
  # prefixes = ["ftree_ecmp", "xpander_ecmp", "xpander_hyb"]

  # Maps storing mapping of active server fraction [key] to average throughput [value]
  ftree_ecmp_throughput_avg = defaultdict(lambda: [])
  xpander_ecmp_throughput_avg = defaultdict(lambda: [])
  xpander_hyb_throughput_avg = defaultdict(lambda: [])
  # Iterate over each topology. 
  for filename in os.listdir(DATA_DIR):
    
    m = re.search('_*_*frac_(\d+)*', filename)
    frac = m.group(1)
    
    avg_list = None
    if filename.startswith("ftree_ecmp"): 
      avg_list = ftree_ecmp_throughput_avg[frac]
    if filename.startswith("xpander_ecmp"): 
      avg_list = xpander_ecmp_throughput_avg[frac]
    if filename.startswith("xpander_hyb"): 
      avg_list = xpander_hyb_throughput_avg[frac]
    # Iterate over each file corresponding to a certain fraction.
    readThroughputFromCSV(avg_list, filename)

  # Now, compute average throughput for each fraction's corresponding throughput list.
  computeAllThroughputAvgs(ftree_ecmp_throughput_avg)
  computeAllThroughputAvgs(xpander_ecmp_throughput_avg)
  computeAllThroughputAvgs(xpander_hyb_throughput_avg)
  print ftree_ecmp_throughput_avg



def main():
  global debug
  debug = True
  if len(sys.argv) < 2:
    print "Usage: sudo python experiment.py [10a|10c|11a|11c]"
    return

  if sys.argv[1] == "10a":
    return

  if sys.argv[1] == "10c":
    generate10c()

  if sys.argv[1] == "11a":
    return

  if sys.argv[1] == "11c":
    return

if __name__ == "__main__":
    main()