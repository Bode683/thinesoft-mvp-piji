FROM postgres:16

# Install pgAudit extension
RUN apt-get update && \
    apt-get install -y postgresql-16-pgaudit && \
    rm -rf /var/lib/apt/lists/*

# Copy configuration files
COPY config/postgresql.conf /etc/postgresql/postgresql.conf
COPY config/pg_hba.conf /etc/postgresql/pg_hba.conf
COPY config/initdb/ /docker-entrypoint-initdb.d/

# Set configuration file location
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf", "-c", "hba_file=/etc/postgresql/pg_hba.conf"]
