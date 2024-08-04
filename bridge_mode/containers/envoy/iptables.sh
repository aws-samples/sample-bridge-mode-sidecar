#!/bin/sh

APP_IP=""
while [ -z $APP_IP ]
do
    APP_IP=$(curl -s ${ECS_CONTAINER_METADATA_URI_V4}/task | jq -r '.Containers[] | select (.Name=="app") | .Networks[0].IPv4Addresses[0]')
    if [ -z $APP_IP ]; then
        sleep 5
    fi
    echo $APP_IP > /tmp/appcontainer
done


iptables -A INPUT -s $APP_IP -j ACCEPT 
iptables -A INPUT -j DROP