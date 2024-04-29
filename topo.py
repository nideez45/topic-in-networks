from mininet.net import Mininet,CLI
from mininet.node import RemoteController,OVSSwitch
from mininet.topo import Topo
import subprocess

def add_script_to_host(host, script_path):
    # Copy the script to the host
    subprocess.call(['sudo', 'cp', script_path, f'/tmp/{script_path.split("/")[-1]}'])
    # Grant execute permissions to the script
    subprocess.call(['sudo', 'chmod', '+x', f'/tmp/{script_path.split("/")[-1]}'])

class SimpleTopology(Topo):
    def build(self):
        # Add two hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        add_script_to_host(h1, 'traffic_gen_h1.sh')
        add_script_to_host(h2, 'traffic_gen_h2.sh')
        # Add one switch
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        # Connect hosts to switch
        self.addLink(s1, s2, bw=10)
        self.addLink(s2, s3, bw=10)
        self.addLink(s3, s4, bw=10)
        self.addLink(s4, s1, bw=10)
        self.addLink(s1, h1, bw=10)
        self.addLink(s3, h2, bw=10)
        self.addLink(s2, h3, bw=10)
        self.addLink(s4, h4, bw=10)
topo = SimpleTopology()

# Set up Mininet using the custom topology and your custom controller
net = Mininet(topo=topo,switch=OVSSwitch, controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6653))

# Start the network
net.start()

net.get('h1').cmd('sh /tmp/traffic_gen_h1.sh &')
net.get('h2').cmd('sh /tmp/traffic_gen_h2.sh &')
net.get('h3').cmd('sh /tmp/traffic_gen_h3.sh &')
net.get('h4').cmd('sh /tmp/traffic_gen_h4.sh &')

# Run Mininet's CLI for testing and exploring
CLI(net)

# Clean up when done
net.stop()