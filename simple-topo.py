# Simple Topology

import os
import math
import random
import networkx as nx
from mininet.topo import Topo

class SimpleTopo(Topo):

    def __init__(self, nswitches=3):

        Topo.__init__(self)

        # Create simple topo for testing purposes
        G = nx.complete_graph(nswitches)
        self.create_topo_from_graph(G)

    def create_topo_from_graph(self, G):
        """ Creates a mininet topology from given networkX graph
        """
        # add switch per node in G
        for n in G.nodes():
            n += 1
            self.addSwitch("s" + str(n))
        
        # connect all switches
        for n1, n2 in G.edges():
            n1 += 1
            n2 += 1
            s1 = "s" + str(n1)
            s2 = "s" + str(n2)
            self.addLink(s1, s2)

        # add one host per switch
        for n in G.nodes():
            n += 1
            mac = '00:00:00:00:00:0' + str(n)
            host = self.addHost("h" + str(n), mac=mac)
            switch = "s" + str(n)
            self.addLink(host, switch)


topos = { 'simple' : (lambda: SimpleTopo()) }