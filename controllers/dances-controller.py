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

	# set dpid of known switches
	self.switch = {}
	self.switch['mi'] = 1229782937975278821
	self.switch['np'] = 15730199386661060610
	self.switch['sc'] = 44159981331328

	# set inital ip-mac table for all known hosts
	self.ip_to_mac = {}
        # mi hosts
	self.ip_to_mac['10.10.1.10'] = "00:60:dd:44:56:70" #tango
	self.ip_to_mac['10.10.1.20'] = "00:0f:53:28:dd:4c" #rumba
	self.ip_to_mac['10.10.1.30'] = "00:0f:53:28:dc:00" #mambo
        #np hosts
	self.ip_to_mac['10.10.2.10'] = "00:60:dd:45:2d:16" #psarch
	self.ip_to_mac['10.10.2.50'] = "00:60:dd:45:91:bb" #tenge
        self.ip_to_mac['10.10.2.30'] = "00:02:c9:45:20:90" #giu3
        self.ip_to_mac['10.10.2.110'] = "00:25:90:14:cc:54" #dennis
        self.ip_to_mac['10.10.2.100'] = "00:02:c9:f0:62:b0" #dxcsbb05
        self.ip_to_mac['10.10.2.101'] = "00:02:c9:f0:62:b0" #dxcsbb05
        self.ip_to_mac['10.10.2.102'] = "00:02:c9:f0:62:b0" #dxcsbb05
        self.ip_to_mac['10.10.2.103'] = "00:02:c9:f0:62:b0" #dxcsbb05
        self.ip_to_mac['10.10.2.104'] = "00:02:c9:f0:62:b0" #dxcsbb05
        self.ip_to_mac['10.10.2.105'] = "00:02:c9:f0:62:b0" #dxcsbb05
        self.ip_to_mac['10.10.2.106'] = "00:02:c9:f0:62:b0" #dxcsbb05
        self.ip_to_mac['10.10.2.107'] = "00:02:c9:f0:62:b0" #dxcsbb05
        #sc hosts
        self.ip_to_mac['10.10.2.210'] = "24:8a:07:6f:87:c0" #twostep
        self.ip_to_mac['10.10.2.200'] = "00:60:dd:45:67:db" #hiphop
        self.ip_to_mac['10.10.2.201'] = "00:60:dd:45:67:db" #hiphop
        self.ip_to_mac['10.10.2.202'] = "00:60:dd:45:67:db" #hiphop
        self.ip_to_mac['10.10.2.203'] = "00:60:dd:45:67:db" #hiphop
        self.ip_to_mac['10.10.2.204'] = "00:60:dd:45:67:db" #hiphop
        self.ip_to_mac['10.10.2.205'] = "00:60:dd:45:67:db" #hiphop
        self.ip_to_mac['10.10.2.206'] = "00:60:dd:45:67:db" #hiphop
        self.ip_to_mac['10.10.2.207'] = "00:60:dd:45:67:db" #hiphop

        self.logger.info("init complete")

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
        #self.add_flow(datapath, 0, match, actions)
	
	self.logger.info("switch_features_handler: %s", datapath)
	
        #self.clear_flows(datapath) # clear existing flows
        self.send_psc_test_config(datapath) # add initial flows


    def send_psc_test_config(self, datapath):
	ofproto = datapath.ofproto
	parser = datapath.ofproto_parser

        controlTable = 10
	dscpTable = 20
	l3Table = 30
        l2Table = 40
        vlanTable = 50       
 

	# install table-miss flow entries for table 10 and 20
	#self.add_goto_to_table(datapath, 0, 10, 20) # not needed on corsa?
        #self.add_goto_to_table(datapath, 0, 20, 30)

	# install all meters on any switch that contacts us
        self.add_meters(datapath)
        
        # send arp to controller (install on any switch that contacts us)
        #match = parser.OFPMatch(eth_type=0x0806)
        #actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        #self.add_flow(datapath, 1, controlTable, match, actions)

	self.logger.info("dpid: %s, mi-dpid: %s", datapath.id, self.switch['mi'])
        if datapath.id == self.switch['mi']:
            self.logger.info("dpid is mi")

           # # test
           # match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.1.10", vlan_vid=(0x1000 | 4010))
           # actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
           # self.add_metered_flow(datapath, 100, l3Table, match, actions, 110)

            # arp
            #match = parser.OFPMatch(eth_type=0x0806)
            #actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
            #self.add_flow(datapath, 1, controlTable, match, actions)

            ## MI hosts ##
            
            # tango
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.1.10", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
 
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.1.10", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
           
            # rumba
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.1.20", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(7), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
 
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.1.20", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(7), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
           
            # mambo
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.1.30", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(3), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
 
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.1.30", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(3), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
           
            ## NP hosts ##
            
            # psarch
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.10", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
            
            # tenge-70
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.50", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            # dennis
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.110", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)


            # giu3
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.30", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)


            # dxcsbb05           
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.100", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.101", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.102", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.103", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.104", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.105", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.106", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.107", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)


            ## NP hosts ## From SC
            
            # psarch
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.10", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
            
            # tenge-70
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.50", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            # dennis
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.110", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)


            # giu3
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.30", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)


            # dxcsbb05           
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.100", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.101", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.102", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.103", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.104", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.105", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.106", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.107", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

 
            ## SC hosts #

            # twostep
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.210", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(10), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)


            # hiphop 
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.200", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(16), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
            

            ## twostep
            #match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.210", vlan_vid=(0x1000 | 4010))
            #actions = [parser.OFPActionOutput(22), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            #self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)


            ## hiphop 
            #match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.200", vlan_vid=(0x1000 | 4010))
            #actions = [parser.OFPActionOutput(22), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            #self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            #match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.201", vlan_vid=(0x1000 | 4010))
            #actions = [parser.OFPActionOutput(22), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            #self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            #match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.202", vlan_vid=(0x1000 | 4010))
            #actions = [parser.OFPActionOutput(22), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            #self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            #match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.203", vlan_vid=(0x1000 | 4010))
            #actions = [parser.OFPActionOutput(22), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            #self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            #match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.204", vlan_vid=(0x1000 | 4010))
            #actions = [parser.OFPActionOutput(22), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            #self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            #match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.205", vlan_vid=(0x1000 | 4010))
            #actions = [parser.OFPActionOutput(22), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            #self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            #match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.206", vlan_vid=(0x1000 | 4010))
            #actions = [parser.OFPActionOutput(22), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            #self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            #match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.207", vlan_vid=(0x1000 | 4010))
            #actions = [parser.OFPActionOutput(22), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            #self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

        if datapath.id == self.switch['np']:
            self.logger.info("dpid is np")

            ## MI hosts ##
            
            # tango
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.1.10", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
            
            # rumba
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.1.20", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
            
            # mambo
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.1.30", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 2)
            
            ## NP hosts ##
            
            # psarch
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.10", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
            
            # tenge-70
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.50", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(3), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            # dennis
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.110", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(7), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)


            # giu3
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.30", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(5), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)


            # dxcsbb05           
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.100", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(12), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.101", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(12), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.102", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(12), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.103", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(12), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.104", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(12), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.105", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(12), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.106", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(12), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.107", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(12), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)


           
            ## SC hosts ##

            # twostep 
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.210", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            # hiphop
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.200", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.201", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.202", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.203", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.204", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.205", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.206", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.207", vlan_vid=(0x1000 | 4010))
            actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)


        if datapath.id == self.switch['sc']:
            self.logger.info("dpid is sc")

            ## MI hosts ##

            # tango
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.1.10", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            # rumba
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.1.20", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
            
            # mambo
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.1.30", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
            
            ## NP hosts ##
            
            # psarch
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.10", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)
            
            # tenge-70
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.50", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            # dennis
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.110", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            # giu3
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.30", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            # dxcsbb05           
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.100", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.101", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.102", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.103", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.104", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.105", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.106", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.107", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(24), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)



            # SC hosts #

            # twostep
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.210", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)


            # hiphop 
            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.200", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.201", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.202", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.203", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.204", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.205", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.206", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)

            match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="10.10.2.207", vlan_vid=(0x1000 | 4049))
            actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4049)), parser.OFPActionSetQueue(0)]
            self.add_metered_flow(datapath, 100, l3Table, match, actions, 1)



    def clear_flows(self, datapath):
    	ofproto = datapath.ofproto
    	parser = datapath.ofproto_parser
   
        match = parser.OFPMatch()
 
    	inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, [])]
    	mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_DELETE,
    		match=match, instructions=inst)
    	datapath.send_msg(mod)

    def add_flow(self, datapath, priority, table, match, actions):
    	ofproto = datapath.ofproto
    	parser = datapath.ofproto_parser
    
    	inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS,
    		actions)]
    	mod = parser.OFPFlowMod(datapath=datapath, table_id=table, priority=priority,
    		match=match, instructions=inst)
    	datapath.send_msg(mod)

    def add_metered_flow(self, datapath, priority, table, match, actions, meter):
    	ofproto = datapath.ofproto
    	parser = datapath.ofproto_parser
    
    	inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS,
    		actions), parser.OFPInstructionMeter(meter)]
    	mod = parser.OFPFlowMod(datapath=datapath, table_id=table, priority=priority,
    		match=match, instructions=inst)
    	datapath.send_msg(mod)
    
    #	self.logger.info("flow added {in_port: %s  eth_dst: %s}", match['in_port'], match['eth_dst'])
    	self.logger.info("\tflow mod sent: %s", mod)

    def add_goto_to_table(self, datapath, priority, table, goto_table):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        match = parser.OFPMatch()
        inst = [parser.OFPInstructionGotoTable(goto_table)]
        mod = parser.OFPFlowMod(datapath=datapath, table_id=table, priority=priority,
        	match=match, instructions=inst)
        datapath.send_msg(mod)

    def add_meters(self, datapath):
    	ofproto = datapath.ofproto
    	parser = datapath.ofproto_parser
    
    	# flags=9 (OFPMF_KBPS + OFPMF_STATS)
    	# flags=13 (KBPS + STATS + BURST)

	# Examples    
    	## 5 Gbps band - burst for WAN BDP=(5Gb x 106ms)=530Mb
    	#wan_band = [parser.OFPMeterBandDrop(type_=ofproto.OFPMBT_DROP, rate=5000000, burst_size=530000)]
    	#
    	## 5 Gbps band - burst for LAN BDP=(5Gb x 0.2ms)=1Mb
    	#lan_band = [parser.OFPMeterBandDrop(type_=ofproto.OFPMBT_DROP, rate=5000000, burst_size=1000)]
    	#
    	## flow meter 1 (LAN) - limit at 5 Gbps
    	#mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=1, bands=lan_band)
    	#datapath.send_msg(mod)
    
    	## flow meter 2 (WAN)- limit at 5 Gbps
    	#mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=2, bands=wan_band)
    	#datapath.send_msg(mod)

	## band definitions
	_1G_band = [parser.OFPMeterBandDrop(type_=ofproto.OFPMBT_DROP, rate=1000000, burst_size=530000)]
	_2G_band = [parser.OFPMeterBandDrop(type_=ofproto.OFPMBT_DROP, rate=2000000, burst_size=530000)]
	_3G_band = [parser.OFPMeterBandDrop(type_=ofproto.OFPMBT_DROP, rate=3000000, burst_size=530000)]
	_4G_band = [parser.OFPMeterBandDrop(type_=ofproto.OFPMBT_DROP, rate=4000000, burst_size=530000)]
	_5G_band = [parser.OFPMeterBandDrop(type_=ofproto.OFPMBT_DROP, rate=5000000, burst_size=530000)]
	max_band = [parser.OFPMeterBandDrop(type_=ofproto.OFPMBT_DROP, rate=4294967295)] # max rate is 0xffffffff == 4294967295

	## meter definitions
        # default non-priority flow (max rate limit)
	mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=1, bands=max_band)
	datapath.send_msg(mod)
        # default non-priority flow (max rate limit)
	mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=2, bands=max_band)
	datapath.send_msg(mod)
	# 1Gpbs meter pool
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=11, bands=_1G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=12, bands=_1G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=13, bands=_1G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=14, bands=_1G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=15, bands=_1G_band)
	datapath.send_msg(mod)

	# 2Gpbs meter pool
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=21, bands=_2G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=22, bands=_2G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=23, bands=_2G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=24, bands=_2G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=25, bands=_2G_band)
	datapath.send_msg(mod)

	# 3Gpbs meter pool
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=31, bands=_3G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=32, bands=_3G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=33, bands=_3G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=34, bands=_3G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=35, bands=_3G_band)
	datapath.send_msg(mod)

	# 4Gpbs meter pool
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=41, bands=_4G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=42, bands=_4G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=43, bands=_4G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=44, bands=_4G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=45, bands=_4G_band)
	datapath.send_msg(mod)

	# 5Gpbs meter pool
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=51, bands=_5G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=52, bands=_5G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=53, bands=_5G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=54, bands=_5G_band)
	datapath.send_msg(mod)
        mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=9, meter_id=55, bands=_5G_band)
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

        self.logger.info("packet in dpid:%s src_mac:%s dst_mac:%s port:%s", dpid, src_mac, dst_mac, port)

        # learn mac address to avoid DROP.
        #self.ip_to_mac[dpid][src_ip] = src_mac

        if dst_ip in self.ip_to_mac:
            dst_mac = self.ip_to_mac[dst_ip]
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

        self.logger.info("packet out dpid:%s src_mac:%s dst_mac:%s port:%s", dpid, src_mac, dst_mac, port)
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

