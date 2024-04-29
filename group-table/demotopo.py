from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import OVSSwitch, Controller, RemoteController
from mininet.log import setLogLevel

class MyTopology(Topo):
    def build(self):
        # Create switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')

        # Create hosts with specified MAC addresses
        h1 = self.addHost('h1', ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2', mac='00:00:00:00:00:02')

        # Connect hosts to switches
        self.addLink(h1, s1)
        self.addLink(h2, s4)

        # Connect switches
        self.addLink(s1, s2)
        self.addLink(s1, s3)
        self.addLink(s2, s4)
        self.addLink(s3, s4)

def setup_custom_arp(net):
    h1 = net.get('h1')
    h2 = net.get('h2')

    # Set custom ARP entry for h1
    h1.setARP('10.0.0.2', '00:00:00:00:00:02')

    # Set custom ARP entry for h2
    h2.setARP('10.0.0.1', '00:00:00:00:00:01')

def run_mininet():
    topo = MyTopology()
    net = Mininet(topo=topo, controller=None, switch=OVSSwitch)
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    net.start()
    # setup_custom_arp(net)
    net.interact()

if __name__ == '__main__':
    setLogLevel('info')
    run_mininet()
