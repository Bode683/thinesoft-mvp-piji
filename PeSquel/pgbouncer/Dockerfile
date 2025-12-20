FROM bitnami/pgbouncer:latest

# Switch to root to install packages
USER root

# Install tools for password hashing
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration and entrypoint
COPY pgbouncer.ini /opt/bitnami/pgbouncer/conf/pgbouncer.ini
COPY entrypoint.sh /opt/bitnami/pgbouncer/custom-entrypoint.sh

# Make sure the entrypoint script is executable and owned by user 1001
RUN chmod +x /opt/bitnami/pgbouncer/custom-entrypoint.sh && \
    chown 1001:1001 /opt/bitnami/pgbouncer/custom-entrypoint.sh

# Switch back to non-root user offered by Bitnami
USER 1001

ENTRYPOINT [ "/opt/bitnami/pgbouncer/custom-entrypoint.sh" ]
CMD [ "pgbouncer", "/opt/bitnami/pgbouncer/conf/pgbouncer.ini" ]
