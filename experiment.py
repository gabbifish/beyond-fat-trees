import os
import sys
import random
import json
import math
import argparse
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

# Runs one permute experiment
# net: Mininet network
# flow_starts: num flow-starts per second (across all servers)
# x: fraction of active servers
# num_seconds: the number of seconds to run simulation for
def experiment_permute(net, flow_starts, x, num_seconds=2, printFrac=True):
    # choose x fraction of servers as active
    num_active_servers = int(len(net.hosts) * x)
    active_servers = random.sample(net.hosts, num_active_servers)

    num_flows_per_server = flow_starts / num_active_servers

    # server -> pid of iperf client processes (so we can wait for process to finish)
    server_to_iperf_pids = defaultdict(list)

    for second in range(0, num_seconds):
        # for each src/dest pair in active server permutation
        for src, dst in pairwise(active_servers):
            # choose flow size from pFabric Web search distribution
            # (NOTE: for now we will just be using the mean of 2.4MB per flow)
            flow_size = '100K'

            if debug:
                print "  Running %d flows of %s bytes each from %s to %s" \
                    % (num_flows_per_server, flow_size, src.name, dst.name)

            port = 5001 + second # scheme for ports: open ports second by second
            output_file = "perm_output/%s_%s_%s_%d_s_%d_src_%s_dst_%s" % \
                (net.topo.name, net.controller.name,
                ('frac' if printFrac else 'lambda'),
                (int(100*x) if printFrac else flow_starts),
                second, src.IP(), dst.IP())
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
            pid_line = src.cmd('echo $!')
            m = re.search('(\d+)', pid_line)
            pid = int(m.group(1))
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
        debug = False

        parser = argparse.ArgumentParser(description=
            'Replicate experiments from "Beyond Fat Trees without antennae, mirrors, and disco balls"')
        parser.add_argument('topo', help='Topology to use: [ftree|xpander]')
        parser.add_argument('routing', help='Routing strategy: [ecmpy|hyb]')
        parser.add_argument('test', help='Test to run: [active-servers|lambda|cli')
        parser.add_argument('num_steps', help='The number of intervals to use in graph',
            type=int, default=10)
        args = parser.parse_args()

        if args.topo == 'ftree':
            topo = FtreeTopo(8, 2)
        elif args.topo == 'xpander':
            topo = XpanderTopo()

        if args.routing == 'ecmp':
            controller = ECMP
        elif args.routing  == 'hyb':
            controller = HYB

        print "Running %s topo with %s controller" % (args.topo, args.routing)
        net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=controller)

        net.start()
        sleep(3)

        if args.test == 'cli':
            CLI(net)
            net.stop()
            return

        try:
            # For graphs 10(a) and 10(c)
            if args.test == "active-servers":
                flow_starts = 32
                num_steps = int(args.num_steps) # Number of intervals to test for
                for x in range(1, num_steps, 1):
                    frac = float(x)/num_steps
                    print "Simulating experiment for active server fraction %f" % (frac)
                    experiment_permute(net, flow_starts, frac)
            
            # For graphs 11(a) and 11(c)
            elif args.test == "lambda":
                print "lambda experiment"
                min_flow_starts = 10
                increment = 10
                max_flow_starts = min_flow_starts + increment*args.num_steps
                for flow_starts in range(min_flow_starts, max_flow_starts, increment):
                    print "Simulating experiment with a load (flow-starts per second) of %d" % (flow_starts)
                    experiment_permute(net, flow_starts, 0.31, printFrac=False)

            # To run a single permute experiment (for testing/development purposes)
            elif args.test == "custom":
                frac = 0.31
                flow_starts = 32
                print "Running Permute(%f) with %d flow_starts" % (frac, flow_starts)
                experiment_permute(net, flow_starts, frac)

            net.stop()
        except: # Make sure to shut down mininet!
            traceback.print_exc()
            net.stop()

if __name__ == "__main__":
    main()
