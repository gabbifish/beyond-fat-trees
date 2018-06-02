import json
import itertools
import re
import matplotlib.pyplot as plt
import csv
import re
from collections import defaultdict, OrderedDict
import sys
import os
import math

debug = None
DATA_DIR = "perm_output/"

def readThroughputFromCSV(arr, filename, idx):
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
      val = int(row[idx])
      # need special parsing for intervals. 
      if idx == 5:
        return #fix!
      arr.append(val)
    f.close()

def generate10a():
  # Maps storing mapping of active server fraction [key] to average fct [value]
  ftree_ecmp_fct_avg = defaultdict(lambda: [])
  xpander_ecmp_fct_avg = defaultdict(lambda: [])
  xpander_hyb_fct_avg = defaultdict(lambda: [])
  # Iterate over each topology. 
  for filename in os.listdir(DATA_DIR):
    m = re.search('_*_*frac_(\d+)*', filename)
    frac = m.group(1)
    
    avg_list = None
    if filename.startswith("ftree_ecmp_frac"): 
      avg_list = ftree_ecmp_throughput_avg[frac]
    if filename.startswith("xpander_ecmp_frac"): 
      avg_list = xpander_ecmp_throughput_avg[frac]
    if filename.startswith("xpander_hyb_frac"): 
      avg_list = xpander_hyb_throughput_avg[frac]
    # Iterate over each file corresponding to a certain fraction, get all bandwidth measurements.
    readThroughputFromCSV(avg_list, filename, 5) 

  generateGraph("10c", ftree_ecmp_throughput_avg, xpander_ecmp_throughput_avg, xpander_hyb_throughput_avg)

def computeAllThroughputAvgs(avg_dict):
  for (key, value) in avg_dict.iteritems():
    avg_dict[key] = sum(value) / len(value)
    avg_dict[key] /= math.pow(10, 6) # Divide by 10^6 to get megabytes

def generate10c():
  # Maps storing mapping of active server fraction [key] to average throughput [value]
  ftree_ecmp_throughput_avg = defaultdict(lambda: [])
  xpander_ecmp_throughput_avg = defaultdict(lambda: [])
  xpander_hyb_throughput_avg = defaultdict(lambda: [])
  # Iterate over each topology. 
  for filename in os.listdir(DATA_DIR):
    m = re.search('_*_*frac_(\d+)*', filename)
    frac = m.group(1)
    
    avg_list = None
    if filename.startswith("ftree_ecmp_frac"): 
      avg_list = ftree_ecmp_throughput_avg[frac]
    if filename.startswith("xpander_ecmp_frac"): 
      avg_list = xpander_ecmp_throughput_avg[frac]
    if filename.startswith("xpander_hyb_frac"): 
      avg_list = xpander_hyb_throughput_avg[frac]
    # Iterate over each file corresponding to a certain fraction, get all bandwidth measurements.
    readThroughputFromCSV(avg_list, filename, 7) 

  generateGraph("10c", ftree_ecmp_throughput_avg, xpander_ecmp_throughput_avg, xpander_hyb_throughput_avg)

def generateGraph(graph, ftree_ecmp_avg, xpander_ecmp_avg, xpander_hyb_avg):
    # Now, compute average throughput for each fraction's corresponding throughput list.
  computeAllThroughputAvgs(ftree_ecmp_avg)
  computeAllThroughputAvgs(xpander_ecmp_avg)
  computeAllThroughputAvgs(xpander_hyb_avg)

  # Sort all dicts in order of ascending keys!
  ftree_ecmp_avg = OrderedDict(sorted(ftree_ecmp_avg.items()))
  xpander_ecmp_avg = OrderedDict(sorted(xpander_ecmp_avg.items()))
  xpander_hyb_avg = OrderedDict(sorted(xpander_hyb_avg.items()))

  # plt.figure()
  plt.plot(ftree_ecmp_avg.keys(), ftree_ecmp_avg.values(), label='ftree-ecmp')
  plt.plot(xpander_ecmp_avg.keys(), xpander_ecmp_avg.values(), label='xpander-ecmp')
  plt.plot(xpander_ecmp_avg.keys(), xpander_ecmp_avg.values(), label='xpander-hyb')

  # Scale y axis appropriately
  plt.ylim(ymax=3)  
  plt.ylim(ymin=0)  

  plt.title('Reproduction of Figure 10c')
  plt.xlabel("% Active servers")
  plt.ylabel("Avg throughput (MB)")
  plt.legend(loc='upper right')
  plt.savefig("10c.png")



def main():
  global debug
  debug = True
  if len(sys.argv) < 2:
    print "Usage: sudo python experiment.py [10a|10c|11a|11c]"
    return

  if sys.argv[1] == "10a":
    generate10a()

  if sys.argv[1] == "10c":
    generate10c()

  if sys.argv[1] == "11a":
    return

  if sys.argv[1] == "11c":
    return

if __name__ == "__main__":
    main()