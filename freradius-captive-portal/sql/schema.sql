-- Création de la base et de l'utilisateur si ce n’est pas déjà fait
-- À exécuter manuellement si ce n’est pas géré dans docker-compose
-- CREATE DATABASE radius;
-- CREATE USER radius WITH PASSWORD 'radiuspass';
-- GRANT ALL PRIVILEGES ON DATABASE radius TO radius;

-- Connexion à la base radius
\c radius;

-- Table des utilisateurs
CREATE TABLE radcheck (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    attribute VARCHAR(64) NOT NULL DEFAULT 'Cleartext-Password',
    op CHAR(2) NOT NULL DEFAULT ':=',
    value VARCHAR(253) NOT NULL
);

-- Attributs supplémentaires en phase d'autorisation
CREATE TABLE radreply (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    attribute VARCHAR(64) NOT NULL,
    op CHAR(2) NOT NULL DEFAULT '=',
    value VARCHAR(253) NOT NULL
);

-- Groupes d’utilisateurs
CREATE TABLE radusergroup (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    groupname VARCHAR(64) NOT NULL,
    priority INT DEFAULT 0
);

-- Attributs appliqués à un groupe
CREATE TABLE radgroupcheck (
    id SERIAL PRIMARY KEY,
    groupname VARCHAR(64) NOT NULL,
    attribute VARCHAR(64) NOT NULL,
    op CHAR(2) NOT NULL DEFAULT ':=',
    value VARCHAR(253) NOT NULL
);

CREATE TABLE radgroupreply (
    id SERIAL PRIMARY KEY,
    groupname VARCHAR(64) NOT NULL,
    attribute VARCHAR(64) NOT NULL,
    op CHAR(2) NOT NULL DEFAULT '=',
    value VARCHAR(253) NOT NULL
);

-- Comptabilité (Accounting)
CREATE TABLE radacct (
    radacctid BIGSERIAL PRIMARY KEY,
    acctsessionid VARCHAR(64) NOT NULL,
    acctuniqueid VARCHAR(32) NOT NULL,
    username VARCHAR(64),
    groupname VARCHAR(64),
    realm VARCHAR(64),
    nasipaddress INET,
    nasportid VARCHAR(15),
    nasporttype VARCHAR(32),
    acctstarttime TIMESTAMP,
    acctupdatetime TIMESTAMP,
    acctstoptime TIMESTAMP,
    acctsessiontime INTEGER,
    acctauthentic VARCHAR(32),
    connectinfo_start VARCHAR(50),
    connectinfo_stop VARCHAR(50),
    acctinputoctets BIGINT,
    acctoutputoctets BIGINT,
    calledstationid VARCHAR(50),
    callingstationid VARCHAR(50),
    acctterminatecause VARCHAR(32),
    servicetype VARCHAR(32),
    framedprotocol VARCHAR(32),
    framedipaddress INET,
    acctstartdelay INTEGER,
    acctstopdelay INTEGER,
    xascendsessionsvrkey VARCHAR(10)
);

-- Authentification réussie
CREATE TABLE radpostauth (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    pass VARCHAR(64),
    reply VARCHAR(32),
    authdate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table des clients (si read_clients = yes)
CREATE TABLE nas (
    id SERIAL PRIMARY KEY,
    nasname VARCHAR(128) NOT NULL,
    shortname VARCHAR(32),
    type VARCHAR(30) DEFAULT 'other',
    ports INTEGER,
    secret VARCHAR(60) NOT NULL,
    server VARCHAR(64),
    community VARCHAR(50),
    description VARCHAR(200)
);

-- Créer l'utilisateur de test
INSERT INTO radcheck (username, attribute, op, value) VALUES ('testuser', 'Cleartext-Password', ':=', 'testpass');

-- Créer un groupe et ajouter l'utilisateur de test à ce groupe
INSERT INTO radusergroup (username, groupname, priority) VALUES ('testuser', 'default_users', 1);

-- Créer des attributs pour le groupe
INSERT INTO radgroupreply (groupname, attribute, op, value) VALUES ('default_users', 'Service-Type', '=', 'Framed-User');
INSERT INTO radgroupreply (groupname, attribute, op, value) VALUES ('default_users', 'Framed-Protocol', '=', 'PPP');
