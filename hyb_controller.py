# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This component is for use with the OpenFlow tutorial.

It acts as a simple hub, but can be modified to act like an L2
learning switch.

It's roughly similar to the one Brandon Heller did for NOX.
"""

from pox.core import core
from pox.lib.packet.ipv4 import ipv4
import pox.openflow.libopenflow_01 as of

import json
import itertools
import random
from datetime import datetime, timedelta
from zlib import crc32
from struct import pack
import networkx as nx
from networkx.readwrite import json_graph

log = core.getLogger()

# flow_hash of packet -> (time_last_pkt_seen, nbytes_sent, path)
# time_last_pkt_seen is for flowlet switching
# nbytes_sent is for switching from ECMP to VLB
flowlet_map = {}

# if time between packets entering network from same flow
# is greater than FLOWLET_DELTA_MICROSEC, then start a new flowlet
FLOWLET_DELTA_MICROSEC = 50

# the routing strategy to use
# can be either ECMP or HYB (HYB is a combination of ECMP and VLB)
routing_strategy = 'HYB'

Q_THRESH = 100000 # 100KB

G = None
filename = 'pox/ext/graph.json'
with open(filename, 'r') as fp:
  data = json.load(fp)
  G = json_graph.adjacency_graph(data)

def ecmp(source, target, graph=G, k=8):
  """
  Returns list of paths according to ecmp algorithm
  """
  return list(itertools.islice(
      nx.all_shortest_paths(graph, source, target), k))

# (src, intermediate, dst) -> physical path
vlb_paths = {}

def bfs(src, dst, g, visited):
  q = []
  q.append([src])

  while len(q) > 0:
    path = q.pop(0) # remove first path in queue
    n = path[len(path) - 1] # get last node in path

    if n not in visited:
      visited.add(n)
      for neighbor in G.neighbors(n):
        new_path = path + [neighbor]
        if neighbor == dst:
          return new_path
        q.append(new_path)

  return None

def get_path_through_node(src, node, dst, graph=G):
  visited = set()
  path1 = bfs(src, node, G, visited)
  if path1 is None:
    print "NO PATH FOUND FROM %d TO %d" % (src, node)
    return

  if dst in path1:
    return path1

  path1.remove(node)
  visited = set(path1)
  path2 = bfs(node, dst, G, visited)
  if path2 is None:
    print "NO PATH FOUND FROM %d TO %d THAT DOESN'T CONTAIN %s" % (node, dst, tuple(path1)) 
    return

  return path1 + path2

def vlb(source, target, graph=G):
  # choose a random intermediary node to go to first
  nodes = list(G.nodes())
  nodes.remove(source)
  intermediate_node = random.choice(nodes)

  # get path to from source to intermediate node then to target
  if (source, intermediate_node, target) not in vlb_paths:
    vlb_paths[(source, intermediate_node, target)] = \
        get_path_through_node(source, intermediate_node, target)
  
  return vlb_paths[(source, intermediate_node, target)]

def ip_to_switch_id(ip):
  parts = [int(x) for x in str(ip).split('.')]
  return parts[-2]

def ip_to_host_id(ip):
  parts = [int(x) for x in str(ip).split('.')]
  return parts[-1]

# Adapted from ripl-pox source code
def flow_hash(packet):
  "Return an 2-tuple hash for TCP/IP packets, otherwise 0."
  hash_input = [0] * 2
  if isinstance(packet.next, ipv4):
    ip = packet.next
    hash_input[0] = ip.srcip.toUnsigned()
    hash_input[1] = ip.dstip.toUnsigned()
    return crc32(pack('LL', *hash_input))
  return 0

# Adapted from ripl-pox source code
def packet_hash(packet):
  "Return an 3-tuple hash for TCP/IP packets, otherwise 0."
  hash_input = [0] * 3
  if isinstance(packet.next, ipv4):
    ip = packet.next
    hash_input[0] = ip.srcip.toUnsigned()
    hash_input[1] = ip.dstip.toUnsigned()
    hash_input[2] = ip.id
    return crc32(pack('LLH', *hash_input))
  return 0

def get_path(source, target, routing_alg='ecmp', G=G):
  # NOTE: routing_alg can be either 'vlb' or 'ecmp'
  if routing_alg == 'ecmp':
    paths = ecmp(source, target)
    return random.choice(paths)
  if routing_alg == 'vlb':
    return vlb(source, target)

class Tutorial (object):
  """
  A Tutorial object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self, connection):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection

    # This binds our PacketIn event listener
    connection.addListeners(self)

    self.dpid = None
    if self.dpid is None:
      self.dpid = connection.dpid

    # Use this table to keep track of which ethernet address is on
    # which switch port (keys are MACs, values are ports).
    self.mac_to_port = {}


  def resend_packet (self, packet_in, out_port):
    """
    Instructs the switch to resend a packet that it had sent to us.
    "packet_in" is the ofp_packet_in object the switch had sent to the
    controller due to a table-miss.
    """
    msg = of.ofp_packet_out()
    msg.data = packet_in

    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    # Send message to switch
    self.connection.send(msg)


  def act_like_hub (self, packet, packet_in):
    """
    Implement hub-like behavior -- send all packets to all ports besides
    the input port.
    """
    # We want to output to all ports -- we do that using the special
    # OFPP_ALL port as the output port.  (We could have also used
    # OFPP_FLOOD.)
    self.resend_packet(packet_in, of.OFPP_ALL)

    # Note that if we didn't get a valid buffer_id, a slightly better
    # implementation would check that we got the full data before
    # sending it (len(packet_in.data) should be == packet_in.total_len)).

  def act_like_switch (self, packet, packet_in):
    """
    Implement switch-like behavior.
    """

    # Learn the port for the source MAC
    print "packet arrived from MAC", packet.src, "on switch", self.dpid, "port", packet_in.in_port
    self.mac_to_port[packet.src] = packet_in.in_port

    # arpp = packet.find('arp')
    # if arpp:
    #   print "arp packet -> flooding out all ports"
    #   self.resend_packet(packet_in, of.OFPP_ALL)
    #   return

    ipp = packet.find('ipv4')
    if ipp:
      print "ip packet with src", ipp.srcip, "and dst", ipp.dstip

    # If we know the out port for the mac destination
    if packet.dst in self.mac_to_port:
      print "found mac destination in map"
      out_port = self.mac_to_port[packet.dst]
      
      # drop packet if it should go out the same port it arrived on
      if out_port == packet_in.in_port:
        print "out_port is the same as in_port... dropping packet"
        return

      # Send packet out the associated port
      print "sending packet out port", out_port
      self.resend_packet(packet_in, out_port)

      # Once you have the above working, try pushing a flow entry
      # instead of resending the packet (comment out the above and
      # uncomment and complete the below.)

      #log.debug("Installing flow...")
      # Maybe the log statement should have source/destination/port?

      #msg = of.ofp_flow_mod()
      #
      ## Set fields to match received packet
      #msg.match = of.ofp_match.from_packet(packet)
      #
      #< Set other fields of flow_mod (timeouts? buffer_id?) >
      #
      #< Add an output action, and send -- similar to resend_packet() >

    else:
      # Flood the packet out everything but the input port
      print 'flooding packet'
      self.resend_packet(packet_in, of.OFPP_ALL)

  def route_packet (self, packet, packet_in):
      # Get destination IP address of packet
      ipdst = None
      arpp = packet.find('arp')
      if arpp:
        ipdst = arpp.protodst
      ipp = packet.find('ipv4')
      if ipp:
        ipdst = ipp.dstip

      
      ##### Forward packet to next hop #####
      
      target_id = ip_to_switch_id(ipdst)
      if self.dpid == target_id:
        # packet dest is host attached to this id
        # hosts are attached to their switch via port 1, so send out port 1
        log.info("target host is attached to this switch")
        host_id = ip_to_host_id(ipdst)
        self.resend_packet(packet_in, host_id)
        return

      # send arp packets along shortest path
      if arpp:
        path = ecmp(self.dpid, target_id, k=1)[0]
        next_hop = path[1]
        log.info("arp")
        self.resend_packet(packet_in, next_hop)
        return

      print "Src: " + str(packet.src)
      print "Dest: " + str(packet.dst)
      print "Event port: " + str(packet_in.in_port)
      
      fhash = flow_hash(packet)
      if fhash not in flowlet_map:
        # this is the first time we are seeing this flow
        # update map with path
        path = get_path(self.dpid, target_id, 'ecmp')
        # fhash -> (time_last_pkt_seen, nbytes_sent, path)
        flowlet_map[fhash] = (datetime.now(), ipp.iplen, path)

      elif packet_in.in_port == 1:
        # this packet was just received from a host
        # update time_last_pkt_seen and nbytes_sent
        (old_time, nbytes_sent, path) = flowlet_map[fhash]
        new_time = datetime.now()
        
        if new_time > old_time + timedelta(microseconds=FLOWLET_DELTA_MICROSEC):
          # start a new flowlet and choose a different path
          routing_alg = 'ecmp'
          if routing_strategy == 'HYB' and nbytes_sent > Q_THRESH:
            routing_alg = 'vlb'
          path = get_path(self.dpid, target_id, routing_alg)

        flowlet_map[fhash] = (new_time, nbytes_sent+ipp.iplen, path)

      path = flowlet_map[fhash][2]
      next_hop_id = path[path.index(self.dpid) + 1]
      self.resend_packet(packet_in, next_hop_id)

  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.

    ipv6p = packet.find('ipv6')
    if not ipv6p:
      #self.act_like_hub(packet, packet_in)
      log.info("packet in")
      #self.act_like_switch(packet, packet_in)
      self.route_packet(packet, packet_in)


def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.info("switch %s has come up" % (event.dpid))
    log.debug("Controlling %s" % (event.connection,))
    Tutorial(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
