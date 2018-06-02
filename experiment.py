import os
import sys
import random
import json
import math
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
from pox.ext.xpander_topo import XpanderTopo
from pox.ext.fattree_topo import FtreeTopo
from subprocess import Popen, PIPE
from time import sleep
import itertools
import traceback

random.seed(1025)
debug = None

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b) 

def iperf_test(hosts, test_type, index=0):
    # host to pid of the iperf client process
    host_to_pid = {}
    for client, server in pairwise(hosts):
        print "  testing throughput from %s to %s" % (client.name, server.name)

        output_file = "iperf_%s_%s_to_%s_%d.txt" % (test_type,
            client.name, server.name, index)
        server_cmd = "iperf -s -p %d &" % (5555)
        client_cmd = "iperf -c %s -p %d %s -t %d > %s &" % (server.IP(),
            5555, ("-P 8" if test_type.endswith("8flow") else ""), 5, output_file)
        
        print "    on %s running command: %s" % (server.name, server_cmd)
        server.sendCmd(server_cmd)
        # wait until command has executed
        server.waitOutput(verbose=True)
        print "    on %s running command: %s" % (client.name, client_cmd)
        client.sendCmd(client_cmd)
        client.waitOutput(verbose=True)
        pid = int(client.cmd('echo $!'))
        host_to_pid[client] = pid

    print "Waiting for iperf tests to finish..."
    for host, pid in host_to_pid.iteritems():
        host.cmd('wait', pid)

    print "Killing all iperf instances..."
    # need to kill iperf instances so we can rerun these tests on the same mininet
    for client, server in pairwise(hosts):
        server.cmd( "kill -9 %iperf" )
        # Wait for iperf server to terminate
        server.cmd( "wait" )

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

# Runs one permute experiment
# net: Mininet network
# flow_starts: num flow-starts per second (across all servers)
# x: fraction of active servers
# num_seconds: the number of seconds to run simulation for
def experiment_permute(net, flow_starts, x, num_seconds):
    # choose x fraction of servers as active
    num_active_servers = int(len(net.hosts) * x)
    active_servers = random.sample(net.hosts, num_active_servers)

    num_flows_per_server = flow_starts / num_active_servers

    # server -> pid of iperf client processes (so we can wait for process to finish)
    server_to_iperf_pids = defaultdict(list)

    # for each second:
    num_seconds = 2
    for second in range(0, num_seconds):
        # for each src/dest pair in active server permutation
        for src, dst in pairwise(active_servers):
            # choose flow size from pFabric Web search distribution
            # (NOTE: for now we will just be using the mean of 2.4MB per flow)
            flow_size = '1M'

            print "  Running %d flows of %s bytes each from %s to %s" \
                % (num_flows_per_server, flow_size, src.name, dst.name)

            port = 5001 + second # scheme for ports: open ports second by second
            output_file = "perm_output/%s_%s_frac_%d_s_%d_src_%s_dst_%s" % (net.topo.name, net.controller.name, int(100*x), second, src.IP(), dst.IP()) 
            num_bytes_per_buffer = "8K"

            # run iperf server on second server
            dst_cmd = "iperf -s -p %d -l %s &" % (port, num_bytes_per_buffer) 

            # run iperf client on first server
            src_cmd = "iperf -c %s -p %d -n %s -P %d -l %s -y C > %s &" \
                % (dst.IP(), port, flow_size, num_flows_per_server,
                    num_bytes_per_buffer, output_file)

            if debug:
                print "    on %s running command: %s" % (dst.name, dst_cmd)
            dst.sendCmd(dst_cmd)
            # wait until command has executed
            dst.waitOutput(verbose=True)
            if debug:
                print "    on %s running command: %s" % (src.name, src_cmd)
            src.sendCmd(src_cmd)
            src.waitOutput(verbose=True)
            pid = int(src.cmd('echo $!'))
            server_to_iperf_pids[src].append(pid)

        # Wait one second after iperf commands are launched.
        sleep(1)

    if debug:
        print "Server to iperf pid dictionary:"
        print server_to_iperf_pids

    print "Waiting for iperf tests to finish..."
    for host, pids in server_to_iperf_pids.iteritems():
        for pid in pids:
            if debug:
                print "waiting for pid %d on host %s" % (pid, host.name)
            host.cmd('wait', pid)
    print "All iperf tests have finished"

    print "Killing all iperf instances..."
    # need to kill iperf instances so we can rerun these tests on the same mininet
    for client, server in pairwise(active_servers):
        server.cmd( "pkill iperf" )
        # Wait for iperf server to terminate
        server.cmd( "wait" )
    print "Done killing all iperf instances"

def main():
        global debug
        debug = True
        if len(sys.argv) < 4:
            print "Usage: sudo python experiment.py [ftree|xpander] [ecmp|hyb] [active-servers|lambda|cli] param"
            return

        if sys.argv[1] == 'ftree':
            topo = FtreeTopo(8, 2)
        elif sys.argv[1] == 'xpander':
            topo = XpanderTopo()

        if sys.argv[2] == 'ecmp':
            controller = ECMP
        elif sys.argv[2] == 'hyb':
            controller = HYB

        print "Running %s topo with %s controller" % (sys.argv[1], sys.argv[2])
        net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=controller)

        net.start()
        sleep(3)

        if sys.argv[3] == 'cli':
            CLI(net)
            net.stop()
            return

        try:
            # If no param passed in as part of active-servers or lambda, this is a problem:
            if len(sys.argv) < 5:
                print "A parameter must be passed in following [active-servers|cli]"

            # For graphs 10(a) and 10(c)
            if sys.argv[3] == "active-servers":
                flow_starts = 32
                num_steps = int(sys.argv[4]) # Distance between active-servers fractions
                num_seconds = 5
                for x in range(1, num_steps, 1):
                    frac = float(x)/num_steps
                    print "Simulating experiment for active server fraction %f" % (frac)
                    experiment_permute(net, flow_starts, frac, num_seconds)
                # experiment_active_server(net) 
            # For graphs 11(a) and 11(c)
            elif sys.argv[3] == "lambda":
                experiment_lambda(net) 
            else:
                print "Please enter \"active-servers\" or \"lambda\' as the second argument."

            net.stop()
        except: # Make sure to shut down mininet!
            traceback.print_exc()
            net.stop()

if __name__ == "__main__":
    main()
