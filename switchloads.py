import os
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import OrderedDict

FILEPATH = 'switchlogs/'

def get_total_npackets(filename):
    with open(FILEPATH+filename, 'r') as fp:
        lines = fp.readlines()
        timestamp, npackets = lines[-1].split(',')
        return int(npackets)

def main():
    ftree = []
    xpander_ecmp = []
    xpander_hyb = []
    for filename in os.listdir(FILEPATH):
        regex = r'switchlog_([a-zA-Z]+)_([a-zA-Z]+)_(\d+)'
        m = re.search(regex, filename)
        if m is None:
            continue
        topo = m.group(1)
        routing = m.group(2)
        switchid = int(m.group(3))

        print "looking at file", filename
        npackets = get_total_npackets(filename)
        print "npackets", npackets

        if topo == 'ftree':
            ftree.append(npackets)
        elif routing == 'ECMP':
            xpander_ecmp.append(npackets)
        elif routing == 'HYB':
            xpander_hyb.append(npackets)

    print ftree
    print xpander_ecmp
    print xpander_hyb

    # Sort all dicts in order of ascending keys
    ftree_vals = sorted(ftree, reverse=True)
    xpander_ecmp_vals = sorted(xpander_ecmp, reverse=True)
    xpander_hyb_vals = sorted(xpander_hyb, reverse=True)

    ftree_x = np.array(range(len(ftree_vals)))
    xpander_ecmp_x = np.array(range(len(xpander_ecmp_vals)))
    xpander_hyb_x = np.array(range(len(xpander_hyb_vals)))

    # plt.bar(ftree_x-0.2, ftree_vals, width=.2, label='ftree-ecmp', align='center')
    # plt.bar(xpander_ecmp_x, xpander_ecmp_vals, width=.2, label='xpander-ecmp', align='center')
    # plt.bar(xpander_hyb_x+0.2, xpander_hyb_vals, width=.2, label='xpander-hyb', align='center')

    plt.plot(ftree_x, ftree_vals, label='ftree-ecmp')
    plt.plot(xpander_ecmp_x, xpander_ecmp_vals, label='xpander-ecmp')
    plt.plot(xpander_hyb_x, xpander_hyb_vals, label='xpander-hyb')

    plt.title("Switch Work Loads")
    plt.legend(loc='upper right')
    plt.xlabel("Switch Rank")
    plt.ylabel("Number of packets")
    plt.savefig("switchloads_line.png")

if __name__ == "__main__":
    main()