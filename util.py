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
from subprocess import Popen, PIPE
from time import sleep
import itertools

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