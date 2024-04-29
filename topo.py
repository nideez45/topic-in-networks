from mininet.net import Mininet,CLI
from mininet.node import RemoteController,OVSSwitch
from mininet.topo import Topo

class SimpleTopology(Topo):
    def build(self):
        # Add two hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')

        # Add one switch
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        # Connect hosts to switch
        self.addLink(s1, s2,)
        self.addLink(s2, s3)
        self.addLink(s3,s4)
        self.addLink(s4,s1)
        self.addLink(s1,h1)
        self.addLink(s3,h2)
        self.addLink(s2,h3)
        self.addLink(s4,h4)

topo = SimpleTopology()

# Set up Mininet using the custom topology and your custom controller
net = Mininet(topo=topo,switch=OVSSwitch, controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6653))

# Start the network
net.start()

# Run Mininet's CLI for testing and exploring
CLI(net)

# Clean up when done
net.stop()