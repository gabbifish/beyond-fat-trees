import os
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import OrderedDict


DIRPATH = ''
# example log line...
# CRITICAL:custom_controller:SWITCH<ID>:<datetime>,<npackets>
def get_packet_counts(filename):
    switchid_to_npackets = {}
    with open(DIRPATH+filename, 'r') as fp:
        line_start = 'CRITICAL:custom_controller:SWITCH'

        for line in fp.readlines():
            if line.startswith(line_start):
                line = line[len(line_start):] # cut line to only relevant info
                switchid_str = line[0:line.index(':')]
                line = line[len(switchid_str)+ 1:]
                switchid = int(switchid_str)
                npackets = int(line.split(',')[1])
                switchid_to_npackets[switchid] = npackets

        return switchid_to_npackets

def main():
    # dicts from switch id to total num packets
    ftree_ecmp = get_packet_counts('ftree_ecmp.log')
    xpander_ecmp = get_packet_counts('xpander_ecmp.log')
    xpander_hyb = get_packet_counts('xpander_hyb.log')

    # get array of values (npackets) from dicts
    ftree_ecmp = [npackets for sid, npackets in ftree_ecmp.iteritems()]
    xpander_ecmp = [npackets for sid, npackets in xpander_ecmp.iteritems()]
    xpander_hyb = [npackets for sid, npackets in xpander_hyb.iteritems()]

    # Sort all arrays in order of descending values
    ftree_vals = sorted(ftree_ecmp, reverse=True)
    xpander_ecmp_vals = sorted(xpander_ecmp, reverse=True)
    xpander_hyb_vals = sorted(xpander_hyb, reverse=True)

    # Convert to numpy arrays
    ftree_x = np.array(range(len(ftree_vals)))
    xpander_ecmp_x = np.array(range(len(xpander_ecmp_vals)))
    xpander_hyb_x = np.array(range(len(xpander_hyb_vals)))

    # Create bar graph
    plt.bar(ftree_x-0.2, ftree_vals, width=.2, label='ftree-ecmp', align='center')
    plt.bar(xpander_ecmp_x, xpander_ecmp_vals, width=.2, label='xpander-ecmp', align='center')
    plt.bar(xpander_hyb_x+0.2, xpander_hyb_vals, width=.2, label='xpander-hyb', align='center')

    plt.title("Switch Work Loads")
    plt.legend(loc='upper right')
    plt.xlabel("Switch Rank")
    plt.ylabel("Number of packets")
    plt.savefig("switchloads.png")

if __name__ == "__main__":
    main()