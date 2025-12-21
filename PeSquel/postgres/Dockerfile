FROM postgres:17-alpine

# Install additional tools if needed
RUN apk add --no-cache bash curl

# Copy initialization scripts (both .sql and .sh files)
COPY init/ /docker-entrypoint-initdb.d/

# Make shell scripts executable
RUN chmod +x /docker-entrypoint-initdb.d/*.sh 2>/dev/null || true

# Copy custom entrypoint
COPY entrypoint.sh /usr/local/bin/custom-entrypoint.sh
RUN chmod +x /usr/local/bin/custom-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/custom-entrypoint.sh"]
CMD ["postgres"]
