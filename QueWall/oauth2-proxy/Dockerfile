FROM quay.io/oauth2-proxy/oauth2-proxy:v7.13.0 AS oauth2-proxy-bin

FROM alpine:3.19

# Copy oauth2-proxy binary from official image
COPY --from=oauth2-proxy-bin /bin/oauth2-proxy /bin/oauth2-proxy

# Copy custom entrypoint
COPY --chmod=755 oauth2-proxy-entrypoint.sh /entrypoint.sh

# Use custom entrypoint
ENTRYPOINT ["/entrypoint.sh"]
