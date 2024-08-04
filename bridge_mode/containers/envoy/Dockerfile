FROM envoyproxy/envoy:v1.31-latest as envoy

FROM public.ecr.aws/amazonlinux/amazonlinux:latest
RUN yum -y update && \
    yum clean all && \
    rm -rf /var/cache/yum

COPY --from=envoy /usr/local/bin/envoy /usr/bin/envoy
RUN yum install -y gettext awscli openssl jq util-linux iptables
COPY envoy.yaml.in /etc/envoy/envoy.yaml.in
COPY launch_envoy.sh /usr/local/bin/launch_envoy.sh
RUN chmod 755 /usr/local/bin/launch_envoy.sh
COPY iptables.sh /usr/local/bin/iptables.sh
RUN chmod 755 /usr/local/bin/iptables.sh

ENTRYPOINT ["launch_envoy.sh"]
