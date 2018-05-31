# Xpander Topology

import os
import math
import random
import json
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
from pox.ext.custom_pox import ECMP
from pox.ext.custom_pox import HYB
from subprocess import Popen, PIPE
from mininet.cli import CLI
from time import sleep
import itertools
from pox.ext.util import *

class XpanderTopo(Topo):

    def __init__(self, n_hosts=12, n_hosts_per_rack=2, n_ports_per_switch=2, k_lift=2):

        self.n_hosts_per_rack = n_hosts_per_rack
        n_switches = int(n_hosts/n_hosts_per_rack)
        n_initial_switches = n_ports_per_switch+1
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

topos = { 'xpander' : (lambda: XpanderTopo()) }
def main():
        # Specify routing algorithm.
        if len(sys.argv) > 1 and sys.argv[1] == "ecmp":
            net = Mininet(topo=XpanderTopo(), host=CPULimitedHost, link = TCLink, controller=ECMP)
        elif len(sys.argv) > 1 and sys.argv[1] == "hyb":
            net = Mininet(topo=XpanderTopo(), host=CPULimitedHost, link = TCLink, controller=HYB)
        else: 
            print "Please enter \"ecmp\" or \"hyb\' as the first argument."
            return

        if sys.argv[2] == 'cli':
            net.start()
            sleep(3)
            CLI(net)
            net.stop()
            return

        # For graphs 10(a) and 10(c)
        if sys.argv[2] == "active-servers":
            experiment_active_server(net) 
        # For graphs 11(a) and 11(c)
        if sys.argv[2] == "lambda":
            experiment_lambda(net) 
        else:
            print "Please enter \"active-servers\" or \"lambda\' as the second argument."

if __name__ == "__main__":
	main()