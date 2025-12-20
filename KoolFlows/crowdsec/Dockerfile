FROM crowdsecurity/crowdsec:latest

# Copy custom configurations
COPY config/acquis.yaml /etc/crowdsec/acquis.yaml
COPY config/profiles.yaml /etc/crowdsec/profiles.yaml

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
