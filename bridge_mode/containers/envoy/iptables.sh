#!/bin/sh

# Locate the 'app' container in this task 
APP_IP=""
while [ -z $APP_IP ]
do
    APP_IP=$(curl -s ${ECS_CONTAINER_METADATA_URI_V4}/task | jq -r '.Containers[] | select (.Name=="app") | .Networks[0].IPv4Addresses[0]')
    if [ -z $APP_IP ]; then
        sleep 5
    fi
done

# Block traffic to envoy unless it comes from the app container
iptables -A INPUT ! -s $APP_IP -p tcp --dport 9090 -j DROP