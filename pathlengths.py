import os
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import OrderedDict

DIRPATH = ''

# CRITICAL:custom_controller:PATH:[7, 10, 12, 8, 9, 11]

def get_path_counts(filename):
    with open(DIRPATH+filename, 'r') as fp:
        line_start = 'CRITICAL:custom_controller:PATH:'
        path_lines = [line[len(line_start):] for line in fp.readlines()
            if line.startswith('CRITICAL:custom_controller:PATH:')]
        path_len_counts = sorted([len(line.split(',')) for line in path_lines])
        return path_len_counts

def main():
    ftree_ecmp = get_path_counts('ftree_ecmp.log')
    xpander_ecmp = get_path_counts('xpander_ecmp.log')
    xpander_hyb = get_path_counts('xpander_hyb.log')
    
    plt.plot(range(len(ftree_ecmp)), ftree_ecmp, label='ftree-ecmp')
    plt.plot(range(len(xpander_ecmp)), xpander_ecmp, label='xpander-ecmp')
    plt.plot(range(len(xpander_hyb)), xpander_hyb, label='xpander-hyb')

    # plt.hist(ftree_ecmp, label='ftree-ecmp')
    # plt.hist(xpander_ecmp, label='xpander-ecmp')
    # plt.hist(xpander_hyb, label='xpander-hyb', align='left')

    plt.title("Path Lengths")
    plt.legend(loc='upper right')
    plt.xlabel("Path Rank")
    plt.ylabel("Length of Path")
    plt.savefig("pathlengths.png")

if __name__ == "__main__":
    main()
