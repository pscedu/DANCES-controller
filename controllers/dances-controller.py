# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Copyright © 2015, Pittsburgh Supercomputing Center.  All Rights Reserved.
#
# This source is a derivative work. The original source is attributed above.
# It was distributed with the Ryu SDN framework availabe here:
# https://github.com/osrg/ryu/

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, arp, vlan
import array

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.ip_to_mac = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        
        #match = parser.OFPMatch()
        #actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
        #                                  ofproto.OFPCML_NO_BUFFER)]
        #self.add_flow(datapath, 0, 0, match, actions)

    def add_flow(self, datapath, table, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, table_id=table, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocol(ethernet.ethernet)
        if not pkt_eth:
            return
        pkt_vlan = pkt.get_protocol(vlan.vlan)
        pkt_arp = pkt.get_protocol(arp.arp)
        if pkt_arp:
            self._handle_arp(datapath, in_port, pkt_eth, pkt_arp, pkt_vlan)
            return
        #pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        #pkt_icmp = pkt.get_protocol(icmp.icmp)
        #if pkt_icmp:
        #    self._handle_icmp(datapath, in_port, pkt_eth, pkt_ipv4, pkt_icmp)
        #    return


    def _handle_arp(self, datapath, port, pkt_ethernet, pkt_arp, pkt_vlan):
        if pkt_arp.opcode != arp.ARP_REQUEST:
            return

        # check for dst_ip's matching MAC #

        dst_mac = pkt_ethernet.dst #unknown value
        src_mac = pkt_ethernet.src
        dst_ip = pkt_arp.dst_ip
        src_ip = pkt_arp.src_ip

        dpid = datapath.id
        self.ip_to_mac.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src_mac, dst_mac, port)

        # learn mac address to avoid DROP.
        self.ip_to_mac[dpid][src_ip] = src_mac

        if dst_ip in self.ip_to_mac[dpid]:
            dst_mac = self.ip_to_mac[dpid][dst_ip]
        else:
             # Requested MAC address is unknown.
             # There is nothing we can do without flood.
             return


        # build arp reply #

        pkt = packet.Packet()
        e = ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
                              dst=src_mac,
                              src=dst_mac)

        v = vlan.vlan(pcp=pkt_vlan.pcp,
                      cfi=pkt_vlan.cfi,
                      vid=pkt_vlan.vid,
                      ethertype=pkt_vlan.ethertype)

        a = arp.arp(opcode=arp.ARP_REPLY,
                    src_mac=dst_mac,
                    src_ip=dst_ip,
                    dst_mac=src_mac,
                    dst_ip=src_ip)

        pkt.add_protocol(e)
        pkt.add_protocol(v)
        pkt.add_protocol(a)

        self._send_packet(datapath, port, pkt)

    def _handle_icmp(self, datapath, port, pkt_ethernet, pkt_ipv4, pkt_icmp):
        if pkt_icmp.type != icmp.ICMP_ECHO_REQUEST:
            return
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
                                           dst=pkt_ethernet.src,
                                           src=self.hw_addr))
        pkt.add_protocol(ipv4.ipv4(dst=pkt_ipv4.src,
                                   src=self.ip_addr,
                                   proto=pkt_ipv4.proto))
        pkt.add_protocol(icmp.icmp(type_=icmp.ICMP_ECHO_REPLY,
                                   code=icmp.ICMP_ECHO_REPLY_CODE,
                                   csum=0,
                                   data=pkt_icmp.data))
        self._send_packet(datapath, port, pkt)

    def _send_packet(self, datapath, port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        self.logger.info("packet-out %s" % (pkt,))
        data = pkt.data
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)

