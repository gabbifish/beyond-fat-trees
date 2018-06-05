# Fat-Tree Topology

# Usage:
# $ sudo mn --custom fattree_topo.py --topo ftree --controller=remote
# $ ryu-manager ./ryu/app/simple_switch_stp_13.py

# Notice:
# Spanning Tree Protocol is important.
# We have tested FtreeTopo(4, 2), (4, 3), (8, 2).

import os
import sys
import json
import networkx as nx
import math
from networkx.readwrite import json_graph
from mininet.topo import Topo

class FtreeTopo(Topo):

    name = "ftree"
    nport  = 4     # Number of ports, even number.
    nlayer = 2     # Number of switch layers.

    ncore  = 0     # Number of core switches.
    nedge  = 0     # Number of edge switches per layer.
    nhost  = 0     # Number of hosts.
    max_hosts_per_edge = 0      # Max number of hosts per edge switch.

    hnodes = []    # host list.
    snodes = []    # switch list.

    G = nx.Graph() # nx graph representation of fat-tree.

    def __init__(self, nport, nlayer):
        self.nport  = nport
        self.nlayer = nlayer

        # Maximum host/switch number.
        # Core switch and Edge switch have the same port number.
        self.nhost  = 2 * (self.nport / 2) ** self.nlayer
        self.nedge  = self.nhost / (self.nport / 2)
        self.ncore  = self.nedge / 2
        self.max_hosts_per_edge = self.nport / 2

        Topo.__init__(self)

        # Create fat-tree topology.
        self.addSwitches()
        self.addLinksAndHosts()

        print "There are %d core switches, %d edge switches, and %d hosts." % (self.ncore, self.nedge, self.nhost)

        self.dump_graph_to_file(self.G)

    def addSwitches(self):
        # Add core switches.
        core = []
        # Add one below because port 0 cannot be used.
        for i in range(self.max_hosts_per_edge + 1, self.ncore + self.max_hosts_per_edge + 1):
            core.append(self.addSwitch("c" + str(i)))
            self.G.add_node(i)

        self.snodes.append(core)

        # Get ceiling multiple of 10 of # of core switches to avoid overlapping core switch 
        # and edge switch numbers.
        factor = math.ceil(math.log10(len(core)))
        factor = math.pow(10, factor)

        # Add edge switches.
        for i in range(1, self.nlayer):
            edge = []
            for j in range(0, self.nedge):
                edge_num = int(factor*i+j)
                self.G.add_node(edge_num)
                edge.append(self.addSwitch("e" + str(edge_num)))
            self.snodes.append(edge)


    def addLinksAndHosts(self):
        # Add links between core and edge switches.
        for i in range(0, self.nedge):
            for j in range(0, self.nport / 2):
                idx = i * (self.nport / 2) % self.ncore + j
                s1 = self.snodes[1][i]
                s2 = self.snodes[0][idx]
                s1_num = int(s1[1:])
                s2_num = int(s2[1:])
                # print "Adding link between switches", s1, s2, "at ports", s2_num, s1_num
                self.addLink(s1, s2, port1=s2_num, port2=s1_num)
                self.G.add_edge(s1_num, s2_num)

        # Add links between each layer of edge switches.
        for i in range(1, self.nlayer - 1):
            for j in range(0, self.nedge):
                for k in range(0, self.nport / 2):
                    tmp = self.nport / 2
                    s1 = self.snodes[i][j]
                    s2 = self.snodes[i + 1][(j // tmp) * tmp + k]
                    s1_num = int(s1[1:])
                    s2_num = int(s2[1:])
                    # print "Adding link between switches", s1, s2, "at ports", s2_num, s1_num
                    self.addLink(s1, s2, port1=s2_num, port2=s1_num)
                    self.G.add_edge(s1_num, s2_num)

        # Add links between edge switches and hosts.
        for i in range(0, self.nedge):
            for j in range(1, self.nport / 2 + 1):
                switch = self.snodes[self.nlayer - 1][i]
                switch_num = int(switch[1:])
                mac = '%s:00:00:00:00:%s' % (str(switch_num).zfill(2), str(j).zfill(2))
                ip = '10.0.%d.%d' % (switch_num, j)
                host = self.addHost("h" + str(switch_num) + "_" + str(j), mac=mac, ip=ip)
                # print "Adding link between host and switch", j, switch_num, "at ports", 1025, j
                self.addLink(host, switch, port1=1025, port2=j)

    def dump_graph_to_file(self, G):
        filename = 'graph.json'
        adj_data = json_graph.adjacency_data(G)
        with open(filename, 'w') as fp:
            json.dump(adj_data, fp)

topos = { 'ftree' : (lambda: FtreeTopo(8, 3)) }
