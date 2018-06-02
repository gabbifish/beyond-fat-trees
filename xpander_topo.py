# Xpander Topology

# Usage:
# $ sudo mn --custom xpander_topo.py --topo xpander --controller=remote

import os
import math
import random
import json
import networkx as nx
from networkx.readwrite import json_graph
from mininet.topo import Topo

random.seed(1025)

class XpanderTopo(Topo):

    def __init__(self, n_hosts=32, n_switches=8, n_initial_switches=4, k_lift=2):

        self.n_hosts_per_rack = int(n_hosts/n_switches) 
        n_lifts = int(math.log(n_switches/n_initial_switches, k_lift))

        print "Creating an initial complete graph of", n_initial_switches, "switches"
        G = nx.complete_graph(n_initial_switches)

        print "Running", n_lifts, (str(k_lift)+"-lift"), "on graph"
        for _ in range(n_lifts):
            G = self.lift_graph(G, k_lift)

        Topo.__init__(self)

        self.create_topo_from_graph(G)

        self.dump_graph_to_file(G)

    def lift_graph(self, old_graph, k):
        """ Performs a k_lift on old_graph as described in section 3.1 of
        "Xpander: Towards Optimal-Performance Datacenters".
        Returns the new graph
        """
        new_graph = nx.Graph()

        old_edges = old_graph.edges()
        next_sid = self.n_hosts_per_rack + 1
        old_nodes_to_new = {} # old nodes to their copies
        for u, v in old_edges:
            # create k copies of u and k copies of v
            # for every edge {u, v} in old graph
            if u not in old_nodes_to_new.keys():
                old_nodes_to_new[u] = [ sid 
                    for sid in range(next_sid, next_sid + k)]
                next_sid += k
            if v not in old_nodes_to_new.keys():
                old_nodes_to_new[v] = [ sid
                    for sid in range(next_sid, next_sid + k)]
                next_sid += k
            u_copies = old_nodes_to_new[u]
            v_copies = old_nodes_to_new[v]
            # TODO: check if ok to add nodes that are already in graph
            new_graph.add_nodes_from(u_copies)
            new_graph.add_nodes_from(v_copies)

            # then create a random matching between
            # the copies of u and the copies of v
            random.shuffle(v_copies)
            new_graph.add_edges_from(
                (u_copies[i], v_copies[i]) for i in range(k))

        return new_graph

    def create_topo_from_graph(self, G):
        """ Creates a mininet topology from given networkX graph
        """
        # add top of rack switch per node in G
        for n in G.nodes():
            self.addSwitch(str(n))
        
        # connect all top of rack switches
        for n1, n2 in G.edges():
            self.addLink(str(n1), str(n2), port1=n2, port2=n1)

        # add hosts for each switch
        for n in G.nodes():
            for h in range(1, self.n_hosts_per_rack+1):
                mac = '%s:00:00:00:00:%s' % (str(n).zfill(2), str(h).zfill(2))
                ip = '10.0.%d.%d' % (n, h)
                host = self.addHost("h" + str(n) + "_" + str(h), mac=mac, ip=ip)
                self.addLink(host, str(n), port1=1025, port2=h)

    def dump_graph_to_file(self, G):
        filename = 'graph.json'
        adj_data = json_graph.adjacency_data(G)
        with open(filename, 'w') as fp:
            json.dump(adj_data, fp)

topos = { 'xpander' : (lambda: XpanderTopo()) }
