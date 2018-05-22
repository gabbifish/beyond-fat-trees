# Xpander Topology

import os
import math
import random
import networkx as nx
from mininet.topo import Topo

class XpanderTopo(Topo):

    def __init__(self, n_hosts=12, n_hosts_per_rack=1, n_ports_per_switch=2, k_lift=2):

        self.n_hosts_per_rack = n_hosts_per_rack
        n_switches = int(n_hosts/n_hosts_per_rack);
        n_initial_switches = n_ports_per_switch+1;
        n_lifts = int(math.log(n_switches/n_initial_switches, k_lift));

        print "Creating an initial complete graph of", n_initial_switches, "switches"
        G = nx.complete_graph(n_initial_switches)

        print "Running", n_lifts, (str(k_lift)+"-lift"), "on graph"
        for _ in range(n_lifts):
            G = self.lift_graph(G, k_lift)

        Topo.__init__(self)

        self.create_topo_from_graph(G)

    def lift_graph(self, old_graph, k):
        """ Performs a k_lift on old_graph as described in section 3.1 of
        "Xpander: Towards Optimal-Performance Datacenters".
        Returns the new graph
        """
        new_graph = nx.Graph()

        old_edges = old_graph.edges()
        for u, v in old_edges:
            # create k copies of u and k copies of v
            # for every edge {u, v} in old graph
            u_copies = [(str(u) + str(i)) for i in range(k)]
            v_copies = [(str(v) + str(i)) for i in range(k)]
            # TODO: check if ok to add nodes that are already in graph
            new_graph.add_nodes_from(u_copies)
            new_graph.add_nodes_from(v_copies)

            # then create a random matching between
            # the copies of u and the copies of v
            random.shuffle(v_copies)
            new_graph.add_edges_from(
                (u_copies[i], v_copies[i]) for i in range(k));

        return new_graph

    def create_topo_from_graph(self, G):
        """ Creates a mininet topology from given networkX graph
        """
        # add top of rack switch per node in G
        for n in G.nodes():
            self.addSwitch(n)
        
        # connect all top of rack switches
        for n1, n2 in G.edges():
            self.addLink(n1, n2)

        # add hosts for each switch
        for switch in G.nodes():
            for h in range(self.n_hosts_per_rack):
                host = self.addHost("h" + switch + "-" + str(h))
                self.addLink(host, switch)


topos = { 'xpander' : (lambda: XpanderTopo()) }
