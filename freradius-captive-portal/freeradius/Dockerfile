FROM ubuntu:22.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    freeradius \
    freeradius-postgresql \
    freeradius-utils \
    freeradius-rest \
    postgresql-client \
    nano \
    iproute2 \
    net-tools \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Configuration des modules
RUN rm -f /etc/freeradius/3.0/sites-enabled/inner-tunnel && \
    rm -f /etc/freeradius/3.0/mods-enabled/eap && \
    ln -s /etc/freeradius/3.0/mods-available/sql /etc/freeradius/3.0/mods-enabled/sql && \
    ln -s /etc/freeradius/3.0/mods-available/rest /etc/freeradius/3.0/mods-enabled/rest

# Copy all custom configurations into the image
COPY clients.conf /etc/freeradius/3.0/clients.conf
COPY mods-available/sql /etc/freeradius/3.0/mods-available/sql
COPY sites-available/default /etc/freeradius/3.0/sites-available/default

# Set correct ownership and permissions at build time
RUN chown -R freerad:freerad /etc/freeradius/3.0 && \
    chmod 640 /etc/freeradius/3.0/clients.conf && \
    chmod 640 /etc/freeradius/3.0/mods-available/sql && \
    chmod 640 /etc/freeradius/3.0/sites-available/default

WORKDIR /etc/freeradius

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 1812/udp 1813/udp

ENTRYPOINT ["/entrypoint.sh"]
