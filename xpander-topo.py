# Xpander Topology

import os
import math
import random
import networkx as nx
from mininet.topo import Topo

class XpanderTopo(Topo):

    def __init__(self, n_hosts, n_hosts_per_rack, n_ports_per_switch=3, k_lift=2):

        self.n_switches = n_hosts/n_hosts_per_rack;
        self.n_initial_switches = n_ports_per_switch+1;
        self.n_lifts = math.log(n_switches/n_initial_switches, k_lift);

        G = nx.complete_graph(n_initial_switches)

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

        nodes_old_to_new = dict() # old node -> [new nodes]
        old_edges = old_graph.edges()
        for u, v in old_edges:
            # create k copies of u and k copies of v
            # for every edge {u, v} in old graph
            if u not in odes_old_to_new.keys():
                nodes_old_to_new[u] = [(str(u) + str(i)) for i in range(k)]
            if v not in nodes_old_to_new.keys();    
                nodes_old_to_new[v] = [(str(v) + str(i)) for i in range(k)]
            u_copies = nodes_old_to_new[u]
            v_copies = nodes_old_to_new[v]
            # todo: CHECK IF CAN ADD nodes that are already in graph
            new_graph.add_nodes_from(u_copies)
            new_graph.add_nodes_from(v_copies)

            # then create a random matching between
            # the copies of u and the copies of v
            random.shuffle(v_copies)
            new_graph.add_edges_from(
                (u_copies[i], v_copies[i]) for i in range(k));

    def create_topo_from_graph(self, G):
        """ Creates a mininet topology from given networkX graph
        """
        pass

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


topos = { 'xpander' : (lambda: XpanderTopo(8, 2)) }
