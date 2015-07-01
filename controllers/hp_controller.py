

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu import utils
import cmd

class PSCSwitch13(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

	def __init__(self, *args, **kwargs):
		super(PSCSwitch13, self).__init__(*args, **kwargs)
		self.mac_to_port = {}

	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def switch_features_handler(self, ev):
		#msg = ev.msg
		#
		#self.logger.debug('OFPSwitchFeatures received: '
		#       'datapath_id=0x%016x n_buffers=%d '
		#       'n_tables=%d auxiliary_id=%d '
		#       'capabilities=0x%08x',
		#       msg.datapath_id, msg.n_buffers, msg.n_tables,
		#       msg.auxiliary_id, msg.capabilities)

        	datapath = ev.msg.datapath
        	ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		#self.add_meters(datapath)

		# install table-miss flow entry
		#
		# We specify NO BUFFER to max_len of the output action due to
		# OVS bug. At this moment, if we specify a lesser number, e.g.,
		# 128, OVS will send Packet-In with invalid buffer_id and
		# truncated packet data. In that case, we cannot output packets
		# correctly.
		match = parser.OFPMatch()
		actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
		 	ofproto.OFPCML_NO_BUFFER)]
        	self.add_flow(datapath, 0, 0, match, actions)

		# install test configuration flows
		self.send_psc_test_config(datapath)

	# install flow entries specific for testing scenario at PSC
	# 3 test hosts:
	# 	new-vm: MAC=90:e2:ba:48:4b:01 ip=147.73.7.101 vlan=4011
	# 	netflow2: MAC=90:e2:ba:48:4b:7d ip=147.73.7.99 vlan=4011
	# 	ps-test: MAC=00:60:dd:44:56:71 ip=147.73.7.82 vlan=4010
	def send_psc_test_config(self, datapath):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		l3Table = 1 
		dscpTable = 1 

		## Best-Effort Flows ##

		## new-vm
	##	match = parser.OFPMatch(vlan_vid=(0x1000 | 4010), eth_dst="90:e2:ba:48:4b:01")
	##	actions = [parser.OFPActionSetField(vlan_vid=(0x1000 | 4011)), parser.OFPActionOutput(1)]
	##	self.add_flow(datapath, 1, match, actions)
	
		## in-bound flows
		#eth_type=0x0800 for ipv4 ethernet header fields (vlans)
		# vlan 4010 -> local path
		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.101", vlan_vid=(0x1000 | 4010))
		actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4011)), parser.OFPActionSetQueue(7)]
		self.add_flow(datapath, 100, l3Table, match, actions)
		#
		# vlan 4011 -> remote path - port 14 vlan 4004
		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.101", vlan_vid=(0x1000 | 4011))
		actions = [parser.OFPActionOutput(14), parser.OFPActionSetField(vlan_vid=(0x1000 | 4004)), parser.OFPActionSetQueue(7)]
		self.add_flow(datapath, 90, l3Table, match, actions)
		#
		# vlan 4003 -> local path
		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.101", vlan_vid=(0x1000 | 4003))
		actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4011)), parser.OFPActionSetQueue(0)]
		self.add_flow(datapath, 80, l3Table, match, actions)
			
		# netflow2
	##	match = parser.OFPMatch(vlan_vid=(0x1000 | 4010), eth_dst="90:e2:ba:48:4b:7d")
	##	actions = [parser.OFPActionSetField(vlan_vid=(0x1000 | 4011)), parser.OFPActionOutput(2)]
	##	self.add_flow(datapath, 1, match, actions)

		## in-bound flows
		#
		# vlan 4010 -> local path
		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.99", vlan_vid=(0x1000 | 4010))
		actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4011)), parser.OFPActionSetQueue(6)]
		self.add_flow(datapath, 100, l3Table, match, actions)
		#
		# vlan 4011 -> remote path - port 14 4003
		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.99", vlan_vid=(0x1000 | 4011))
		actions = [parser.OFPActionOutput(14), parser.OFPActionSetField(vlan_vid=(0x1000 | 4003)), parser.OFPActionSetQueue(6)]
		self.add_flow(datapath, 90, l3Table, match, actions)
		#
		# vlan 4004 -> local path
		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.99", vlan_vid=(0x1000 | 4004))
		actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4011)), parser.OFPActionSetQueue(1)]
		self.add_flow(datapath, 80, l3Table, match, actions)

		## ps-test ##
		#
		## in-bound flows
		#
		# vlan 4011 -> local path
		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.82", vlan_vid=(0x1000 | 4011))
		actions = [parser.OFPActionOutput(13), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(5)]
		self.add_flow(datapath, 100, l3Table, match, actions)
		# vlan 4010 -> local path
		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.82", vlan_vid=(0x1000 | 4010))
		actions = [parser.OFPActionOutput(13), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(5)]
		self.add_flow(datapath, 100, l3Table, match, actions)


#		## Priority Flows ##
#
#		## new-vm
#		## in-bound flows
#		# eth_type=0x0800 for ipv4 ethernet header fields (vlans)
#		# vlan 4010 -> local path
#		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.101", vlan_vid=(0x1000 | 4010), ip_dscp=22)
#		actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4011)), parser.OFPActionSetQueue(7)]
#		self.add_flow(datapath, 100, dscpTable, match, actions)
#		#
#		# vlan 4011 -> remote path
#		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.101", vlan_vid=(0x1000 | 4011), ip_dscp=22)
#		actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4011)), parser.OFPActionSetQueue(7)]
#		self.add_flow(datapath, 90, dscpTable, match, actions)
#		#
#		# vlan 4003 -> local path
#		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.101", vlan_vid=(0x1000 | 4003), ip_dscp=22)
#		actions = [parser.OFPActionOutput(1), parser.OFPActionSetField(vlan_vid=(0x1000 | 4011)), parser.OFPActionSetQueue(7)]
#		self.add_flow(datapath, 80, dscpTable, match, actions)
#			
#		# netflow2
#		## in-bound flows
#		#
#		# vlan 4010 -> local path
#		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.99", vlan_vid=(0x1000 | 4010), ip_dscp=22)
#		actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4011)), parser.OFPActionSetQueue(7)]
#		self.add_flow(datapath, 100, dscpTable, match, actions)
#		#
#		# vlan 4011 -> remote path
#		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.99", vlan_vid=(0x1000 | 4011), ip_dscp=22)
#		actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4011)), parser.OFPActionSetQueue(7)]
#		self.add_flow(datapath, 90, dscpTable, match, actions)
#		#
#		# vlan 4004 -> local path
#		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.99", vlan_vid=(0x1000 | 4004), ip_dscp=22)
#		actions = [parser.OFPActionOutput(2), parser.OFPActionSetField(vlan_vid=(0x1000 | 4011)), parser.OFPActionSetQueue(7)]
#		self.add_flow(datapath, 80, dscpTable, match, actions)
#
#		## ps-test ##
#		## in-bound flows
#		#
#		# vlan 4011 -> local path
#		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.82", vlan_vid=(0x1000 | 4011), ip_dscp=22)
#		actions = [parser.OFPActionOutput(15), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(7)]
#		self.add_flow(datapath, 100, dscpTable, match, actions)
#		# vlan 4010 -> local path
#		match = parser.OFPMatch(eth_type=0x0800, ipv4_dst="147.73.7.82", vlan_vid=(0x1000 | 4010), ip_dscp=22)
#		actions = [parser.OFPActionOutput(15), parser.OFPActionSetField(vlan_vid=(0x1000 | 4010)), parser.OFPActionSetQueue(7)]
#		self.add_flow(datapath, 100, dscpTable, match, actions)

	def add_flow(self, datapath, priority, table, match, actions):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
			actions)]
		mod = parser.OFPFlowMod(datapath=datapath, table_id=table, priority=priority,
			match=match, instructions=inst)
		datapath.send_msg(mod)

	#	self.logger.info("flow added {in_port: %s  eth_dst: %s}", match['in_port'], match['eth_dst'])
		self.logger.info("\tflow mod sent: %s", mod)
		
	def add_metered_flow(self, datapath, priority, match, actions, meter):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		inst = [parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS,
			actions), parser.OFPInstructionMeter(meter)]
		mod = parser.OFPFlowMod(datapath=datapath, table_id=1, priority=priority,
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

	#	self.logger.info("flow added {in_port: %s  eth_dst: %s}", match['in_port'], match['eth_dst'])
		self.logger.info("\tflow mod sent: %s", mod)

	def request_meter_features(self, datapath):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		req = parser.OFPMeterFeaturesStatsRequest(datapath, 0)
		datapath.send_msg(req)

	def add_meters(self, datapath):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
	
		# remote flow meter - limit at 5 Gbps
		bands = [parser.OFPMeterBandDrop(type_=ofproto.OFPMBT_DROP, rate=5000000, burst_size=500000)]
		mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=13, meter_id=1, bands=bands)
		datapath.send_msg(mod)

		# local flow meter - limit at 5 Gbps
		bands = [parser.OFPMeterBandDrop(type_=ofproto.OFPMBT_DROP, rate=5000000, burst_size=500000)]
		# flags=9 (OFPMF_KBPS + OFPMF_STATS)
		# flags=13 (KBPS + STATS + BURST)
		mod = parser.OFPMeterMod(datapath=datapath, command=ofproto.OFPMC_ADD, flags=13, meter_id=2, bands=bands)
		datapath.send_msg(mod)

	def send_flow_stats_request(self, datapath, ofport):
		ofp = datapath.ofproto
		ofp_parser = datapath.ofproto_parser

		cookie = cookie_mask = 0

		match = ofp_parser.OFPMatch(in_port=ofport)
		request = ofp_parser.OFPFlowStatsRequest(datapath, 0, ofp.OFPTT_ALL,
			ofp.OFPP_ANY, ofp.OFPG_ANY, cookie, cookie_mask, match)

		datapath.send_msg(request)

	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		msg = ev.msg
		datapath = msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		in_port = msg.match['in_port']

		pkt = packet.Packet(msg.data)
		eth = pkt.get_protocols(ethernet.ethernet)[0]

		dst = eth.dst
		src = eth.src

		dpid = datapath.id
		self.mac_to_port.setdefault(dpid, {})

		self.logger.info("--\n\t-> packet-in:\t port: %s; %s", in_port, eth)

		# learn a mac address to avoid FLOOD next time.
		self.mac_to_port[dpid][src] = in_port

		if dst in self.mac_to_port[dpid]:
		    out_port = self.mac_to_port[dpid][dst]
		else:
		    out_port = ofproto.OFPP_FLOOD

		actions = [parser.OFPActionOutput(out_port)]

		self.logger.info("\t<- packet-out:\tport: %s\n--\n", out_port)

		# install a flow to avoid packet_in next time
		if out_port != ofproto.OFPP_FLOOD:
		    match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
		    self.add_flow(datapath, 1, match, actions)

		data = None
		if msg.buffer_id == ofproto.OFP_NO_BUFFER:
		    data = msg.data

		out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
					  in_port=in_port, actions=actions, data=data)
		datapath.send_msg(out)
	
		#self.logger.info("* Sending stats request for port %s", in_port)	
		#self.send_flow_stats_request(datapath, in_port)

	@set_ev_cls(ofp_event.EventOFPErrorMsg,
		[HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
	def error_msg_handler(self,ev):
		msg = ev.msg
		self.logger.info('OFPErrorMsg received: type=0x%02x code=0x%02x', msg.type, msg.code)

	@set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
	def flow_stats_reply_handler(self, ev):
		flows = []
		for stat in ev.msg.body:
			flows.append('table_id=%s '
				'duration_sec=%d duration_nsec=%d '
				'priority=%d '
				'idle_timeout=%d hard_timeout=%d flags=0x%04x '
				'cookie=%d packet_count=%d byte_count=%d '
				'match=%s instructions=%s' %
				(stat.table_id,
				stat.duration_sec, stat.duration_nsec,
				stat.priority,
				stat.idle_timeout, stat.hard_timeout, stat.flags,
				stat.cookie, stat.packet_count, stat.byte_count,
				stat.match, stat.instructions))
		self.logger.info('FlowStats: %s', ev.msg)		
