#!/usr/bin/env python3

"""Shortest Path Switching template
CSCI1680

This example creates a simple controller application that watches for
topology events.  You can use this framework to collect information
about the network topology and install rules to implement shortest
path switching.

"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0

from ryu.topology import event, switches
import ryu.topology.api as topo

from ryu.lib.packet import packet, ether_types
from ryu.lib.packet import ethernet, arp, icmp

from ofctl_utils import OfCtl, VLANID_NONE

from topo_manager_example import *
import queue

DEFAULT_COOKIE = 0
DEFAULT_PRIORITY=0

class ShortestPathSwitching(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]


    def __init__(self, *args, **kwargs):
        super(ShortestPathSwitching, self).__init__(*args, **kwargs)

        self.tm = TopoManager()

    def add_forwarding_rule(self, datapath, dl_dst, port):
        ofctl = OfCtl.factory(datapath, self.logger)

        actions = [datapath.ofproto_parser.OFPActionOutput(port)]
        ofctl.set_flow(cookie=DEFAULT_COOKIE, priority=DEFAULT_PRIORITY,
                                    dl_type=ether_types.ETH_TYPE_IP,
                                    dl_vlan=VLANID_NONE,
                                    dl_dst=dl_dst,
                                    actions=actions)
        print('forwarding_rule:\ndl_dst: %s\nport: %s'%(dl_dst,port))
        

    @set_ev_cls(event.EventSwitchEnter)
    def handle_switch_add(self, ev):
        """
        Event handler indicating a switch has come online.
        """
        switch = ev.switch

        self.logger.warn("Added Switch switch%d with ports:", switch.dp.id)
        for port in switch.ports:
            self.logger.warn("\t%d:  %s", port.port_no, port.hw_addr)

        # TODO:  Update network topology and flow rules
        sw_name = "switch_{}".format(switch.dp.id)
        tm_switch = TMSwitch(sw_name,switch)
        self.tm.add_switch(tm_switch)
        # test
        # self.add_forwarding_rule(switch.dp,'00:00:00:00:00:01',1)
        # self.add_forwarding_rule(switch.dp,'00:00:00:00:00:02',2)
        print("shoudong: %s"%(switch.dp))
        # --------------------------------------------------------------------------- 
        self.updateAll()

    def updateAll(self):
        for device in self.tm.all_devices:
            if isinstance(device,TMHost):
                self.bfsUpdate(device)

    @set_ev_cls(event.EventSwitchLeave)
    def handle_switch_delete(self, ev):
        """
        Event handler indicating a switch has been removed
        """
        switch = ev.switch

        self.logger.warn("Removed Switch switch%d with ports:", switch.dp.id)
        for port in switch.ports:
            self.logger.warn("\t%d:  %s", port.port_no, port.hw_addr)

        # TODO:  Update network topology and flow rules
        tm_switch = self.tm.find_tmswitch_by_switch(switch)
        self.tm.deleteSwitch(tm_switch)
        self.updateAll()

    @set_ev_cls(event.EventHostAdd)
    def handle_host_add(self, ev):
        """
        Event handler indiciating a host has joined the network
        This handler is automatically triggered when a host sends an ARP response.
        """
        host = ev.host
        self.logger.warn("Host Added:  %s (IPs:  %s) on switch%s/%s (%s)",
                          host.mac, host.ipv4,
                         host.port.dpid, host.port.port_no, host.port.hw_addr)

        # TODO:  Update network topology
        tm_switch = self.tm.find_switch_by_port(host.port)
        print(tm_switch)
        h_name = "host_{}".format(host.mac)
        tm_host = TMHost(h_name, host)
        tm_host.add_neighbor(tm_switch)
        tm_switch.add_neighbor(tm_host)
        self.tm.add_host(tm_host)
        tm_switch.set_pm_table(host.port.port_no, tm_host.get_mac())
        print(tm_switch.pm_table)
        #TODO: update flow rules
        self.bfsUpdate(tm_host)

    def bfsUpdate(self, host):
        visited = []
        q = queue.Queue()
        q.put(host)
        dst_mac = host.get_mac()
        while(not q.empty()):
            device = q.get()
            for n in device.get_neighbors():
                if n in visited:
                    break
                visited.append(n)
                q.put(n)
                if isinstance(n,TMSwitch):
                    if isinstance(device, TMHost):
                        h_mac = device.get_mac()
                        s_port = n.get_link_port(h_mac)
                        #set flow table and father node
                        print("dp: %s, dst_mac: %s, s_port: %s"%(n.get_dp(),dst_mac,s_port))
                        print("dst_mac type: %s\ns_port type: %s"%(type(dst_mac),type(s_port)))
                        self.add_forwarding_rule(n.switch.dp,dst_mac,s_port)
                        n.setFather(device)
                    elif isinstance(device,TMSwitch):
                        ports = device.get_ports()
                        for d_port in ports:
                            if d_port in n.pm_table:
                                s_port = n.get_link_port(d_port.hw_addr)
                                # set flow table and father node
                                
                                self.add_forwarding_rule(n.get_dp(),dst_mac,s_port)
                                n.setFather(device)
                                break
                elif isinstance(n,TMHost):
                    # add father
                    n.setFather(device)
        


    @set_ev_cls(event.EventLinkAdd)
    def handle_link_add(self, ev):
        """
        Event handler indicating a link between two switches has been added
        """
        link = ev.link
        src_port = ev.link.src
        dst_port = ev.link.dst
        self.logger.warn("Added Link:  switch%s/%s (%s) -> switch%s/%s (%s)",
                         src_port.dpid, src_port.port_no, src_port.hw_addr,
                         dst_port.dpid, dst_port.port_no, dst_port.hw_addr)

        # TODO:  Update network topology and flow rules
        tm_switch1 = self.tm.find_switch_by_port(src_port)
        tm_switch2 = self.tm.find_switch_by_port(dst_port)

        tm_switch1.add_neighbor(tm_switch2)
        tm_switch2.add_neighbor(tm_switch1)
        # tm_switch1.set_pm_table()


    @set_ev_cls(event.EventLinkDelete)
    def handle_link_delete(self, ev):
        """
        Event handler indicating when a link between two switches has been deleted
        """
        link = ev.link
        src_port = link.src
        dst_port = link.dst

        self.logger.warn("Deleted Link:  switch%s/%s (%s) -> switch%s/%s (%s)",
                          src_port.dpid, src_port.port_no, src_port.hw_addr,
                          dst_port.dpid, dst_port.port_no, dst_port.hw_addr)

        # TODO:  Update network topology and flow rules

    @set_ev_cls(event.EventPortModify)
    def handle_port_modify(self, ev):
        """
        Event handler for when any switch port changes state.
        This includes links for hosts as well as links between switches.
        """
        port = ev.port
        self.logger.warn("Port Changed:  switch%s/%s (%s):  %s",
                         port.dpid, port.port_no, port.hw_addr,
                         "UP" if port.is_live() else "DOWN")

        # TODO:  Update network topology and flow rules

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
       EventHandler for PacketIn messages
        """
        msg = ev.msg

        # In OpenFlow, switches are called "datapaths".  Each switch gets its own datapath ID.
        # In the controller, we pass around datapath objects with metadata about each switch.
        dp = msg.datapath

        # Use this object to create packets for the given datapath
        ofctl = OfCtl.factory(dp, self.logger)

        in_port = msg.in_port
        pkt = packet.Packet(msg.data)# resolve packet out
        eth = pkt.get_protocols(ethernet.ethernet)[0]# get link layer protocal

        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            arp_msg = pkt.get_protocols(arp.arp)[0]# resolve package as arp msg

            if arp_msg.opcode == arp.ARP_REQUEST: # if it is a request option

                self.logger.warning("Received ARP REQUEST on switch%d/%d:  Who has %s?  Tell %s",
                                    dp.id, in_port, arp_msg.dst_ip, arp_msg.src_mac)

                # Generate a *REPLY* for this request based on your switch state
                ask_ip = arp_msg.src_ip
                ask_mac = arp_msg.src_mac
                repl_ip = arp_msg.dst_ip
                repl_mac =self. tm.ARPTable[repl_ip]
                # Here is an example way to send an ARP packet using the ofctl utilities
                ofctl.send_arp(arp_opcode=arp.ARP_REPLY,vlan_id=VLANID_NONE,dst_mac=ask_mac,sender_mac=repl_mac,sender_ip=repl_ip,
                              target_mac=ask_mac, target_ip=ask_ip, src_port=ofctl.dp.ofproto.OFPP_CONTROLLER,output_port=in_port
                              )

                print("send reply!")

