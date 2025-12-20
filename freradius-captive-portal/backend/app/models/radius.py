from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class RadCheck(Base):
    """
    Table radcheck - stocke les informations d'authentification des utilisateurs
    Colonnes typiques dans une base FreeRADIUS:
    - id: identifiant unique
    - username: nom de l'utilisateur
    - attribute: attribut à vérifier (généralement 'Cleartext-Password')
    - op: opérateur de comparaison (généralement '==')
    - value: valeur de l'attribut (mot de passe en clair ou hashé)
    """
    __tablename__ = 'radcheck'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, index=True)
    attribute = Column(String(64), nullable=False)
    op = Column(String(2), nullable=False)
    value = Column(String(253), nullable=False)
    
    def __repr__(self):
        return f"<RadCheck(username='{self.username}', attribute='{self.attribute}')>"

class RadReply(Base):
    """
    Table radreply - stocke les attributs à retourner lors de l'authentification réussie
    Colonnes typiques dans une base FreeRADIUS:
    - id: identifiant unique
    - username: nom de l'utilisateur
    - attribute: nom de l'attribut RADIUS à renvoyer
    - op: opérateur (généralement '=')
    - value: valeur de l'attribut à renvoyer
    """
    __tablename__ = 'radreply'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, index=True)
    attribute = Column(String(64), nullable=False)
    op = Column(String(2), nullable=False)
    value = Column(String(253), nullable=False)
    
    def __repr__(self):
        return f"<RadReply(username='{self.username}', attribute='{self.attribute}', value='{self.value}')>"

class RadUserGroup(Base):
    """
    Table radusergroup - associe les utilisateurs à des groupes
    """
    __tablename__ = 'radusergroup'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, index=True)
    groupname = Column(String(64), nullable=False)
    priority = Column(Integer, nullable=False, default=1)
    
    def __repr__(self):
        return f"<RadUserGroup(username='{self.username}', groupname='{self.groupname}')>"

class RadGroupReply(Base):
    """
    Table radgroupreply - attributs à retourner pour un groupe d'utilisateurs
    """
    __tablename__ = 'radgroupreply'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    groupname = Column(String(64), nullable=False, index=True)
    attribute = Column(String(64), nullable=False)
    op = Column(String(2), nullable=False)
    value = Column(String(253), nullable=False)
    
    def __repr__(self):
        return f"<RadGroupReply(groupname='{self.groupname}', attribute='{self.attribute}')>"


class RadAcct(Base):
    """
    Table radacct - stocke les informations de comptabilité des sessions utilisateur
    Colonnes typiques dans une base FreeRADIUS:
    - radacctid: identifiant unique de l'enregistrement
    - acctsessionid: identifiant de la session
    - acctuniqueid: identifiant unique de la session
    - username: nom de l'utilisateur
    - nasipaddress: adresse IP du NAS
    - acctstarttime: heure de début de la session
    - acctupdatetime: heure de la dernière mise à jour
    - acctstoptime: heure de fin de la session
    - acctinterval: intervalle entre les mises à jour
    - acctsessiontime: durée de la session en secondes
    - acctinputoctets: octets reçus
    - acctoutputoctets: octets envoyés
    - calledstationid: identifiant de la station appelée (BSSID du point d'accès)
    - callingstationid: identifiant de la station appelante (MAC du client)
    - framedipaddress: adresse IP attribuée au client
    - acctterminatecause: raison de la fin de la session
    """
    __tablename__ = 'radacct'
    __table_args__ = {'extend_existing': True}
    
    radacctid = Column(BigInteger, primary_key=True)
    acctsessionid = Column(String(64), nullable=False)
    acctuniqueid = Column(String(32), nullable=False)
    username = Column(String(64))
    realm = Column(String(64))
    nasipaddress = Column(String(15), nullable=False)
    nasportid = Column(String(15))
    nasporttype = Column(String(32))
    acctstarttime = Column(DateTime, nullable=False)
    acctupdatetime = Column(DateTime)
    acctstoptime = Column(DateTime)
    # La colonne acctinterval n'existe pas dans la base de données PostgreSQL
    acctsessiontime = Column(Integer)
    acctauthentic = Column(String(32))
    connectinfo_start = Column(String(50))
    connectinfo_stop = Column(String(50))
    acctinputoctets = Column(BigInteger)
    acctoutputoctets = Column(BigInteger)
    calledstationid = Column(String(50))
    callingstationid = Column(String(50))
    acctterminatecause = Column(String(32))
    servicetype = Column(String(32))
    framedprotocol = Column(String(32))
    framedipaddress = Column(String(15))
    
    def __repr__(self):
        return f"<RadAcct(username='{self.username}', session='{self.acctsessionid}')>"
