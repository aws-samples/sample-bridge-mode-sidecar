# Bridge mode envoy sigv4 sidecar

To deploy:

cdk bootstrap
cdk deploy 

How it works:
- Cdk creates two containers in an ECS task, with bridge mode
- On boot, each container will identify the other from ECS task metadata, using the iptables.sh scripts
-- app container will add DNAT iptables rules to force port 80 lattice traffic to the envoy sidecar
-- envoy container will add iptables rule to prevent incoming traffic from any container but the app container
- envoy container is configured to accept tcp inbound on port 9090 and connect using TLS upstream to an arbitrary host.

Notes:
- envoy is configured to use the system CA chain. If your lattice services have custom certificates, you will need to update the chain
- Only traffic destined to the lattice service network using IPv4 is handled from the app container

