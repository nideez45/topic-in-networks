#!/bin/bash

# Server IP address and port
SERVER_IP="10.0.0.2"

# Run iperf in server mode
echo "Starting iperf server..."
iperf -s -u  &

# Sleep to allow server to start
sleep 2

# Run iperf in client mode
echo "Starting iperf client..."
iperf -c $SERVER_IP -u  --bandwidth 7M -P 20 

# Terminate iperf server
killall iperf
