FROM quay.io/keycloak/keycloak:23.0

# Switch to root to add the wrapper script
USER root

# Copy entrypoint script
COPY entrypoint.sh /custom-entrypoint.sh
RUN chmod 755 /custom-entrypoint.sh

# Entrypoint to read secrets and call kc.sh
ENTRYPOINT ["/bin/bash", "/custom-entrypoint.sh"]
CMD ["start-dev", "--import-realm"]
