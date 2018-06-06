import matplotlib
matplotlib.use('Agg')
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
THROUGHPUT_IDX = 8
INTERVAL_IDX = 6
FRAC_RE = '_*_*frac_(\d+)*'
LAMBDA_RE = '_*_*lambda_(\d+)*'

def readIperfParamFromCSV(arr, filename, idx):
  # CSV headers:
  # 0 = timestamp
  # 1 = source_address
  # 2 = source_port
  # 3 = destination_address
  # 4 = destination_port
  # 5 = direction
  # 6 = interval
  # 7 = transferred_bytes
  # 8 = bits_per_second      
  with open(DATA_DIR+filename, 'rb') as f:
    reader = csv.reader(f)
    for row in reader:
      val = row[idx]
      # need special parsing for intervals
      if idx == INTERVAL_IDX:
        m = re.search('(\d+.\d+)-(\d+.\d+)', val)
        start = float(m.group(1))
        end = float(m.group(2))
        val = end - start #computing flow duration.
      arr.append(float(val))
    f.close()

def computeAllThroughputAvgs(avg_dict, rescale_to_MB=False):
  for (key, value) in avg_dict.iteritems():
    if len(value) == 0:
      avg_dict[key] = 0
      continue
    avg_dict[key] = sum(value) / len(value)
    if rescale_to_MB:
      avg_dict[key] /= math.pow(10, 6) # Divide by 10^6 to get megabytes

def generate(graph_name):
  # Maps storing mapping of active server fraction or load [key] to average throughput (a) OR FCT (c) [value]
  ftree_ecmp_avg = defaultdict(lambda: [])
  xpander_ecmp_avg = defaultdict(lambda: [])
  xpander_hyb_avg = defaultdict(lambda: [])
  # Iterate over each topology. 
  for filename in os.listdir(DATA_DIR):
    regex =  FRAC_RE if '10' in graph_name else LAMBDA_RE
    m = re.search(regex, filename)
    if m is None:
      continue # ignore improperly formatted file
    xval = int(m.group(1))
    
    avg_list = None
    xlabel = 'frac' if '10' in graph_name else 'lambda'
    if filename.startswith("ftree_ecmp_" + xlabel): 
      avg_list = ftree_ecmp_avg[xval]
    if filename.startswith("xpander_ecmp_" + xlabel): 
      avg_list = xpander_ecmp_avg[xval]
    if filename.startswith("xpander_hyb_" + xlabel): 
      avg_list = xpander_hyb_avg[xval]
    # Iterate over each file corresponding to a certain fraction, get all bandwidth measurements.
    idx = INTERVAL_IDX if 'a' in graph_name else THROUGHPUT_IDX
    readIperfParamFromCSV(avg_list, filename, idx) 

  generateGraph(graph_name, ftree_ecmp_avg, xpander_ecmp_avg, xpander_hyb_avg)

def generateGraph(graph_name, ftree_ecmp_avg, xpander_ecmp_avg, xpander_hyb_avg):
  # Now, compute average throughput for each fraction's corresponding throughput list.
  rescale_to_MB = True if "c" in graph_name else False

  computeAllThroughputAvgs(ftree_ecmp_avg, rescale_to_MB)
  computeAllThroughputAvgs(xpander_ecmp_avg, rescale_to_MB)
  computeAllThroughputAvgs(xpander_hyb_avg, rescale_to_MB)

  # Sort all dicts in order of ascending keys!
  ftree_ecmp_avg = OrderedDict(sorted(ftree_ecmp_avg.items()))
  xpander_ecmp_avg = OrderedDict(sorted(xpander_ecmp_avg.items()))
  xpander_hyb_avg = OrderedDict(sorted(xpander_hyb_avg.items()))

  if debug:
    print "ftree_ecmp_avg", ftree_ecmp_avg
    print "xpander_ecmp_avg", xpander_ecmp_avg
    print "xpander_hyb_avg", xpander_hyb_avg

  plt.plot(ftree_ecmp_avg.keys(), ftree_ecmp_avg.values(), label='ftree-ecmp')
  plt.plot(xpander_ecmp_avg.keys(), xpander_ecmp_avg.values(), label='xpander-ecmp')
  plt.plot(xpander_hyb_avg.keys(), xpander_hyb_avg.values(), label='xpander-hyb')

  plt.title("Reproduction of Figure %s" % (graph_name))
  if "10" in graph_name:
    plt.xlabel("% Active servers")
  else:
    plt.xlabel("flow-starts per second")

  if "a" in graph_name:
    plt.ylabel("Flow completion time (s)")
  else:
    plt.ylabel("Avg throughput (MB)")

  # Scale y axis appropriately
  if "a" in graph_name:
    plt.ylim(ymax=3)  
    plt.ylim(ymin=0)
  else:
    plt.ylim(ymax=5)  
    plt.ylim(ymin=0)  

  plt.legend(loc='upper right')
  plt.savefig("%s.png" % (graph_name))

def main():
  global debug
  debug = True
  if len(sys.argv) < 2:
    print "Usage: sudo python analysis.py [10a|10c|11a|11c]"
    return

  graph_name = sys.argv[1]
  generate(graph_name)

if __name__ == "__main__":
    main()
