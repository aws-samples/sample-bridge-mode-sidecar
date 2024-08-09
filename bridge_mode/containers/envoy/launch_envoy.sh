#!/bin/sh

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
/usr/local/bin/iptables.sh

cat /etc/envoy/envoy.yaml.in | envsubst \$DEPLOY_REGION > /etc/envoy/envoy.yaml
capsh --drop="cap_net_admin" -- -c "envoy -l trace -c /etc/envoy/envoy.yaml"
