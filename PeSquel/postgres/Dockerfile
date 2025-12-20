FROM postgres:17-alpine

# Install additional tools if needed
RUN apk add --no-cache bash curl

# Copy initialization scripts
COPY init/*.sql /docker-entrypoint-initdb.d/

# Copy custom entrypoint
COPY entrypoint.sh /usr/local/bin/custom-entrypoint.sh
RUN chmod +x /usr/local/bin/custom-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/custom-entrypoint.sh"]
CMD ["postgres"]
