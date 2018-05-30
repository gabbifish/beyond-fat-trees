# Fat-Tree Topology
# @author: andy

# Usage:
# $ sudo mn --custom fattree-topo.py --topo ftree --controller=remote
# $ ryu-manager ./ryu/app/simple_switch_stp_13.py

# Notice:
# Spanning Tree Protocol is important.
# I have test FtreeTopo(4, 2), (4, 3), (8, 2).

import os
import sys
import networkx as nx
from networkx.readwrite import json_graph
from mininet.topo import Topo
from collections import defaultdict
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI
sys.path.append("../../")
from pox.ext.jelly_pox import ECMP
from pox.ext.jelly_pox import HYB
from subprocess import Popen, PIPE
from time import sleep
import itertools
from pox.ext.util import *

class FtreeTopo(Topo):

    nport  = 4     # Number of ports, even number.
    nlayer = 2     # Number of switch layers.

    ncore  = 0     # Number of core switches.
    nedge  = 0     # Number of edge switches per layer.
    nhost  = 0     # Number of hosts.

    hnodes = []    # host list.
    snodes = []    # switch list.

    def __init__(self, nport, nlayer):
        self.nport  = nport
        self.nlayer = nlayer

        # Maximum host/switch number.
        # Core switch and Edge switch have the same port number.
        self.nhost  = 2 * (self.nport / 2) ** self.nlayer
        self.nedge  = self.nhost / (self.nport / 2)
        self.ncore  = self.nedge / 2

        Topo.__init__(self)

        # Create fat-tree topology.
        self.addHosts()
        self.addSwitches()
        self.addLinks()


    def addHosts(self):
        for i in range(0, self.nhost):
            self.hnodes.append(self.addHost("h" + str(i)))


    def addSwitches(self):
        # Add core switches.
        core = []
        for i in range(0, self.ncore):
            core.append(self.addSwitch("c" + str(i)))

        self.snodes.append(core)

        # Add edge switches.
        for i in range(1, self.nlayer):
            edge = []
            for j in range(0, self.nedge):
                edge.append(self.addSwitch("e" + str(i) + str(j)))
            self.snodes.append(edge)


    def addLinks(self):
        # Add links between core and edge switches.
        for i in range(0, self.nedge):
            for j in range(0, self.nport / 2):
                idx = i * (self.nport / 2) % self.ncore + j
                self.addLink(self.snodes[1][i], self.snodes[0][idx])

        # Add links between each layer of edge switches.
        for i in range(1, self.nlayer - 1):
            for j in range(0, self.nedge):
                for k in range(0, self.nport / 2):
                    tmp = self.nport / 2
                    self.addLink(self.snodes[i][j],
                                 self.snodes[i + 1][(j // tmp) * tmp + k])

        # Add links between edge switches and hosts.
        for i in range(0, self.nedge):
            for j in range(0, self.nport / 2):
                self.addLink(self.snodes[self.nlayer - 1][i],
                             self.hnodes[self.nport / 2 * i + j])

def experiment_active_server(net):
    print "Starting active server experiment"
    net.start()
    # sleep to wait for switches to come up and connect to controller
    sleep(3)

    num_runs = 5
    
    print "Running TCP 1-flow experiment on jellyfish"
    for i in range(0, num_runs):
        iperf_test(net.hosts, "ecmp_1flow", i)

    print "Running TCP 8-flow experiment on jellyfish"
    for i in range(0, num_runs):
        iperf_test(net.hosts, "ecmp_8flow", i)
   
    print "Done with active server experiment for fct"
    net.stop()

def experiment_lambda(net):
    print "Starting lambda / flow-starts per second experiment"
    net.start()
    # sleep to wait for switches to come up and connect to controller
    sleep(3)

    num_runs = 5
    
    print "Running TCP 1-flow experiment on jellyfish"
    for i in range(0, num_runs):
        iperf_test(net.hosts, "ecmp_1flow", i)

    print "Running TCP 8-flow experiment on jellyfish"
    for i in range(0, num_runs):
        iperf_test(net.hosts, "ecmp_8flow", i)
   
    print "Done with active server experiment for fct"
    net.stop()

topos = { 'ftree' : (lambda: FtreeTopo(8, 2)) }
def main():
        # Specify routing algorithm.
        ftree = FtreeTopo(8, 2)
        if len(sys.argv) > 1 and sys.argv[1] == "ecmp":
            net = Mininet(topo=ftree, host=CPULimitedHost, link = TCLink, controller=ECMP)
        elif len(sys.argv) > 1 and sys.argv[1] == "hyb":
            net = Mininet(topo=ftree, host=CPULimitedHost, link = TCLink, controller=HYB)
        else: 
            print "Please enter \"ecmp\" or \"hyb\' as the first argument."
            return

        # For graphs 10(a) and 10(c)
        if sys.argv[2] == "active-servers":
            experiment_active_server(net) 
        # For graphs 11(a) and 11(c)
        if sys.argv[2] == "lambda":
            experiment_lambda(net) 
        else:
            print "Please enter \"active-servers\" or \"lambda\' as the second argument."