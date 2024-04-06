from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet,arp,ipv4
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.topology.api import get_switch, get_link
from ryu.topology import event, switches
from collections import defaultdict
import queue
# switches
switches = []

# mapping between mac address and dpid,port
# dpid is used to identify each switch
mymacs = {}

#mapping between ip address and dpid,port
myips = {}

# adjacency map [sw1][sw2]->port from sw1 to sw2
adjacency = defaultdict(lambda:defaultdict(lambda:None))

# ARP Cache
arp_cache = {}
 

def get_path(src, dst, start_port, final_port):
    # executing Dijkstra's algorithm
    print( "get_path function is called, src=", src," dst=", dst, " first_port=", start_port, " final_port=", final_port)
    
    # defining dictionaries for saving each node's distance and its parent node in the path from first node to that node
    distance = {}
    parent = {}

    # setting initial distance of every node to infinity
    for dpid in switches:
        distance[dpid] = 100000
        parent[dpid] = None

    # setting distance of the source to 0
    distance[src] = 0

    # creating a set of all nodes
    Q = queue.PriorityQueue()
    for dpid in switches:
        Q.put((-distance[dpid],dpid))

    
    while not Q.empty():
        # getting closest node from source
        dist,u = Q.get()
        print(dist,u)
        for p in switches:
            # if u and other switches are adjacent
            if adjacency[u][p] != None:
                # assuming link weight of 1
                if distance[u] + 1 < distance[p]:
                    distance[p] = distance[u] + 1
                    parent[p] = u
                    Q.put((-distance[p],p))

    # creating a list of switches between src and dst which are in the shortest path obtained by Dijkstra's algorithm reversely
    r = []
    p = dst
    r.append(p)
    # set q to the last node before dst 
    q = parent[p]
    while q is not None:
        if q == src:
            r.append(q)
            break
        p = q
        r.append(p)
        q = parent[p]

    r.reverse()

    # setting path 
    if src == dst:
        path=[src]
    else:
        path=r

    # Now adding in_port and out_port to the path
    r = []
    in_port = start_port
    for s1, s2 in zip(path[:-1], path[1:]):
        out_port = adjacency[s1][s2]
        r.append((s1, in_port, out_port))
        in_port = adjacency[s2][s1]
    r.append((dst, in_port, final_port))
    return r

 

class ProjectController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ProjectController, self).__init__(*args, **kwargs)
        self.datapath_list = []

    def install_mac_path(self,p, msg, src_mac, dst_mac):
        print("PATH installing for ARP reply")
        print( "p=", p, " src_mac=", src_mac, " dst_mac=", dst_mac)
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # adding path to flow table of each switch inside the shortest path
        for sw, in_port, out_port in p:
            print("installing flow rule on",sw)
            print(src_mac,dst_mac,in_port,out_port)
            match = parser.OFPMatch(in_port=in_port,eth_type=ether_types.ETH_TYPE_ARP, eth_src=src_mac, eth_dst=dst_mac)
            # setting actions part of the flow table
            actions = [parser.OFPActionOutput(out_port)]
            # getting the datapath
            datapath = self.datapath_list[int(sw)-1]
            # getting instructions based on the actions
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS , actions)]
            mod = datapath.ofproto_parser.OFPFlowMod(datapath=datapath, match=match, idle_timeout=0, hard_timeout=0,
                                                     priority=1, instructions=inst)
            # finalizing the change to switch datapath
            datapath.send_msg(mod)
        return

    def install_ip_path(self, p, msg, src_ip, dst_ip):
        print("PATH installing for IP based routing")
        print( "p=", p, " src_ip=", src_ip, " dst_ip=", dst_ip)
        #    msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # adding path to flow table of each switch inside the shortest path
        for sw, in_port, out_port in p:
            print("installing flow rule on",sw)
            print(src_ip,dst_ip,in_port,out_port)
            match = parser.OFPMatch(in_port=in_port,eth_type=ether_types.ETH_TYPE_IP, ipv4_src=src_ip, ipv4_dst=dst_ip)
            # setting actions part of the flow table
            actions = [parser.OFPActionOutput(out_port)]
            # getting the datapath
            datapath = self.datapath_list[int(sw)-1]
            # getting instructions based on the actions
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS , actions)]
            mod = datapath.ofproto_parser.OFPFlowMod(datapath=datapath, match=match, idle_timeout=0, hard_timeout=0,
                                                     priority=1, instructions=inst)
            # finalizing the change to switch datapath
            datapath.send_msg(mod)

 
    # defining event handler for setup and configuring of switches
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures , CONFIG_DISPATCHER)
    def switch_features_handler(self , ev):
        print("switch_features_handler function is called")
        # getting the datapath, ofproto and parser objects of the event
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # setting match condition to nothing so that it will match to anything
        match = parser.OFPMatch()
        # setting action to send packets to OpenFlow Controller without buffering
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS , actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
                            datapath=datapath, match=match, cookie=0,
                            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
                            priority=0, instructions=inst)
        
        datapath.send_msg(mod)

 
    # defining an event handler for packets coming to switches event
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # getting msg, datapath, ofproto and parser objects
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # getting the port switch received the packet with
        in_port = msg.match['in_port']
        # parse the raw packet data 
        pkt = packet.Packet(msg.data)
        #  extract the Ethernet header information from the received packet
        eth = pkt.get_protocol(ethernet.ethernet)

        # avoid broadcasts from LLDP 
        if eth.ethertype == ether_types.ETH_TYPE_LLDP or eth.ethertype == ether_types.ETH_TYPE_IPV6:
            return
        # add the host to the mymacs of the first switch that gets the packet
        
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        if src not in mymacs.keys():
            mymacs[src] = (dpid, in_port)
            print("mymacs=", mymacs)

        # Handle ARP packets
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            self.handle_arp_packet(msg, datapath, in_port, pkt)
        # Handle IP packets
        elif eth.ethertype == ether_types.ETH_TYPE_IP:
            self.handle_ip_packet(datapath,parser,msg,ofproto,in_port,pkt)

    def handle_arp_packet(self, msg, datapath, in_port, pkt):
        arp_pkt = pkt.get_protocol(arp.arp)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        if arp_pkt.src_ip not in myips:
            myips[arp_pkt.src_ip] = (datapath.id,in_port)

        # Check if it's an ARP request
        if arp_pkt.opcode == arp.ARP_REQUEST:
            # Check the ARP cache for the requested IP
            if arp_pkt.dst_ip in arp_cache:
                # Respond with the MAC address from the cache
                print("arp cache hit")
                self.send_arp_reply(datapath, in_port, arp_cache[arp_pkt.dst_ip],arp_pkt.src_mac,arp_pkt.dst_ip,arp_pkt.src_ip)
            else:
                print("arp cache miss")
                # Flood the ARP request (with appropriate broadcast handling)
                self.flood_arp_request(msg, datapath, in_port)

        # Check if it's an ARP reply
        elif arp_pkt.opcode == arp.ARP_REPLY:
            # Update the ARP cache with the sender's IP and MAC
            arp_cache[arp_pkt.src_ip] = arp_pkt.src_mac
                # Get the switch and port for the destination MAC
            dst_dpid, dst_port = mymacs[arp_pkt.dst_mac]
            # Get the path to the destination switch
            path = get_path(datapath.id, dst_dpid, in_port, dst_port)
            self.install_mac_path(path, msg, arp_pkt.src_mac, arp_pkt.dst_mac)
            
            # Forward the packet along the installed path
            out_port = path[0][2]
            actions = [parser.OFPActionOutput(out_port)]
            data = msg.data
            out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                                    in_port=in_port, actions=actions, data=data)
            datapath.send_msg(out)
                

    def send_arp_reply(self, datapath, in_port,src_mac, dst_mac, src_ip, dst_ip):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        actions = [parser.OFPActionOutput(in_port)]
        arp_reply = packet.Packet()
        arp_reply.add_protocol(ethernet.ethernet(dst=dst_mac,src=src_mac))
        arp_reply.add_protocol(arp.arp(opcode=arp.ARP_REPLY,src_mac=src_mac, src_ip=src_ip,
                                   dst_mac=dst_mac, dst_ip=dst_ip))
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                                in_port=ofproto.OFPP_CONTROLLER, actions=actions,
                                data=arp_reply.data)
        datapath.send_msg(out)

    def flood_arp_request(self, msg, datapath, in_port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                in_port=in_port, actions=actions, data=msg.data)
        datapath.send_msg(out)


    def handle_ip_packet(self,datapath,parser,msg,ofproto,in_port,pkt):
        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        # getting source and destination of the link
        src = ipv4_pkt.src
        dst = ipv4_pkt.dst
        print("IP based routing for src=",src,"dst=",dst)
        p = get_path(myips[src][0], myips[dst][0], myips[src][1], myips[dst][1])
        self.install_ip_path(p, msg, src, dst)
        print("installed path=", p)
        out_port = p[0][2]

        actions = [parser.OFPActionOutput(out_port)]

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
                                actions=actions, data=data)
        datapath.send_msg(out)
        
    events = [event.EventSwitchEnter,
              event.EventSwitchLeave, event.EventPortAdd,
              event.EventPortDelete, event.EventPortModify,
              event.EventLinkAdd, event.EventLinkDelete]
    @set_ev_cls(events)
    def get_topology_data(self, ev):
        global switches
        switch_list = get_switch(self, None)  
        
        # storing the dpid of all switch
        switches = [switch.dp.id for switch in switch_list]
        
        # storing the datapath of all switch, to install rules
        self.datapath_list = [switch.dp for switch in switch_list]
        self.datapath_list.sort(key=lambda dp: dp.id)
        
        # getting the links between all switches
        links_list = get_link(self, None)
        mylinks = [(link.src.dpid,link.dst.dpid,link.src.port_no,link.dst.port_no) for link in links_list]

        # s1 -- port1 ====== port2 -- s2
        for s1, s2, port1, port2 in mylinks:
            adjacency[s1][s2] = port1
            adjacency[s2][s1] = port2