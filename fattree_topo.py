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
from networkx.readwrite import json_graph
from mininet.topo import Topo

class FtreeTopo(Topo):

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
        # self.addHosts()
        self.addLinks()

        self.dump_graph_to_file(self.G)

    # def addHosts(self):
        # for i in range(0, self.nhost):
            # mac = '%s:00:00:00:00:%s' % (str(n).zfill(2), str(h).zfill(2))
            # ip = '10.0.%d.%d' % (n, h)
            # host = self.addHost("h" + str(n) + "_" + str(h), mac=mac, ip=ip)
            # self.hnodes.append(self.addHost("h" + str(i)))

    def addSwitches(self):
        # Add core switches.
        core = []
        # Add one below because port 0 cannot be used.
        for i in range(self.max_hosts_per_edge + 1, self.ncore + self.max_hosts_per_edge + 1):
            core.append(self.addSwitch("c" + str(i)))
            self.G.add_node(i)

        self.snodes.append(core)

        # Add edge switches.
        for i in range(1, self.nlayer):
            edge = []
            for j in range(0, self.nedge):
                self.G.add_node(10*i+j)
                edge.append(self.addSwitch("e" + str(i) + str(j)))
            self.snodes.append(edge)


    def addLinks(self):
        # Add links between core and edge switches.
        for i in range(0, self.nedge):
            for j in range(0, self.nport / 2):
                idx = i * (self.nport / 2) % self.ncore + j
                s1 = self.snodes[1][i]
                s2 = self.snodes[0][idx]
                # self.addLink(s1, s2)
                s1_num = int(s1[1:])
                s2_num = int(s2[1:])
                # self.G.add_edge(s1_num, s2_num)
                # print "HELLO"
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
                    # print "HELLO"
                    # print "Adding link between switches", s1, s2, "at ports", s2_num, s1_num
                    self.addLink(s1, s2, port1=s2_num, port2=s1_num)
                    self.G.add_edge(s1_num, s2_num)

        # Add links between edge switches and hosts.
        # print "ADDING HOST TO SWITCH LINKS"
        for i in range(0, self.nedge):
            for j in range(1, self.nport / 2 + 1):
                # print i, j
                switch = self.snodes[self.nlayer - 1][i]
                switch_num = int(switch[1:])
                # print switch_num, j
                mac = '%s:00:00:00:00:%s' % (str(switch_num).zfill(2), str(j).zfill(2))
                ip = '10.0.%d.%d' % (switch_num, j)
                # print "Added", mac, ip
                host = self.addHost("h" + str(switch_num) + "_" + str(j), mac=mac, ip=ip)
                # self.addLink(switch, host)
                # print "j"
                # print "Adding link between host and switch", j, switch_num, "at ports", 1025, j
                self.addLink(host, switch, port1=1025, port2=j)
                # self.addLink(host, switch)

    def dump_graph_to_file(self, G):
        # print nx.to_dict_of_dicts(G)
        filename = 'graph.json'
        adj_data = json_graph.adjacency_data(G)
        with open(filename, 'w') as fp:
            json.dump(adj_data, fp)

topos = { 'ftree' : (lambda: FtreeTopo(4, 2)) }
