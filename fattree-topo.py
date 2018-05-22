# Fat-Tree Topology
# @author: andy

# Usage:
# $ sudo mn --custom fattree-topo.py --topo ftree --controller=remote
# $ ryu-manager ./ryu/app/simple_switch_stp_13.py

# Notice:
# Spanning Tree Protocol is important.
# I have test FtreeTopo(4, 2), (4, 3), (8, 2).

import os

from mininet.topo import Topo

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


topos = { 'ftree' : (lambda: FtreeTopo(8, 2)) }
