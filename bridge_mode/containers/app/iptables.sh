#!/bin/sh

# Locate the signing sidecar in this task 
ENVOY_IP=""
while [ -z $ENVOY_IP ]
do
    ENVOY_IP=$(curl -s ${ECS_CONTAINER_METADATA_URI_V4}/task | jq -r '.Containers[] | select (.Name=="envoy") | .Networks[0].IPv4Addresses[0]')
    if [ -z $ENVOY_IP ]; then
        sleep 5
    fi
done

# Send IPV4 VPC Lattice traffic to this sidecar
iptables -t nat -A OUTPUT -p tcp -d 169.254.171.0/24 --dport 80  -j DNAT --to-destination $ENVOY_IP:9090
iptables -t nat -A INPUT -p tcp -m conntrack --ctstate RELATED,ESTABLISHED

# Call original application, but drop cap_net_admin beforehand
capsh --drop="cap_net_admin" -- -c $"tail -f /dev/null"