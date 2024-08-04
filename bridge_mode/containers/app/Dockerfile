FROM public.ecr.aws/amazonlinux/amazonlinux:latest
RUN yum -y update && \
    yum clean all && \
    rm -rf /var/cache/yum
RUN yum install jq awscli iptables gettext -y
COPY iptables.sh /usr/local/bin/iptables.sh
RUN chmod 755 /usr/local/bin/iptables.sh
ENTRYPOINT ["/usr/local/bin/iptables.sh"]