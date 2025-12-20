from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class RadAcct(Base):
    """
    Modèle pour la table radacct de FreeRADIUS - stocke les données d'accounting.
    
    Cette table contient toutes les sessions utilisateurs, actives et terminées,
    ainsi que les informations de consommation de bande passante.
    """
    __tablename__ = 'radacct'
    __table_args__ = {'extend_existing': True}

    # Clé primaire
    radacctid = Column(BigInteger, primary_key=True)

    # Identifiants de session
    acctsessionid = Column(String(64), nullable=False, index=True)
    acctuniqueid = Column(String(32), nullable=False, unique=True, index=True)
    
    # Identifiants utilisateur/équipement
    username = Column(String(64), nullable=True, index=True)
    realm = Column(String(64), nullable=True)
    
    # Identifiants NAS (Network Access Server)
    nasipaddress = Column(String(15), nullable=False, index=True)
    nasportid = Column(String(15), nullable=True)
    nasporttype = Column(String(32), nullable=True)
    
    # Temps de session
    acctstarttime = Column(DateTime, nullable=True, index=True)
    acctupdatetime = Column(DateTime, nullable=True)
    acctstoptime = Column(DateTime, nullable=True, index=True)
    # La colonne acctinterval n'existe pas dans la base de données PostgreSQL
    acctsessiontime = Column(Integer, nullable=True, index=True)  # Durée de la session en secondes
    acctauthentic = Column(String(32), nullable=True)
    connectinfo_start = Column(String(50), nullable=True)
    connectinfo_stop = Column(String(50), nullable=True)
    acctinputoctets = Column(BigInteger, nullable=True)  # Octets reçus (download)
    acctoutputoctets = Column(BigInteger, nullable=True)  # Octets envoyés (upload)
    calledstationid = Column(String(50), nullable=True)
    callingstationid = Column(String(50), nullable=True, index=True)  # MAC address de l'utilisateur
    acctterminatecause = Column(String(32), nullable=True)  # Raison de fin de session
    servicetype = Column(String(32), nullable=True)
    framedprotocol = Column(String(32), nullable=True)
    framedipaddress = Column(String(15), nullable=True, index=True)  # IP attribuée à l'utilisateur
    # Colonnes IPv6 non présentes dans la base PostgreSQL
    # framedipv6address = Column(String(45), nullable=True)
    # framedipv6prefix = Column(String(45), nullable=True)
    # framedinterfaceid = Column(String(44), nullable=True)
    # delegatedipv6prefix = Column(String(45), nullable=True)
    
    def __repr__(self):
        return f"<RadAcct(username='{self.username}', session='{self.acctsessionid}')>"
    
    @property
    def is_active(self):
        """Détermine si la session est active (pas de acctstoptime)"""
        return self.acctstoptime is None
    
    @property
    def duration_seconds(self):
        """Durée de la session en secondes"""
        if self.acctsessiontime:
            return self.acctsessiontime
        
        if self.acctstarttime:
            if self.acctstoptime:
                return int((self.acctstoptime - self.acctstarttime).total_seconds())
            else:
                # Session active, calculer la durée jusqu'à maintenant
                return int((datetime.utcnow() - self.acctstarttime).total_seconds())
        
        return 0
    
    @property
    def total_octets(self):
        """Total des octets transmis (upload + download)"""
        input_octets = self.acctinputoctets or 0
        output_octets = self.acctoutputoctets or 0
        return input_octets + output_octets
    
    @property
    def total_megabytes(self):
        """Total des mégaoctets transmis"""
        return round(self.total_octets / (1024 * 1024), 2)

class NASInfo(Base):
    """
    Modèle pour la table nas de FreeRADIUS - stocke les informations sur les points d'accès.
    """
    __tablename__ = 'nas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nasname = Column(String(128), nullable=False, index=True)  # IP ou nom DNS du NAS
    shortname = Column(String(32), nullable=True)
    type = Column(String(30), nullable=True, default='other')  # Type de NAS (cisco, etc.)
    ports = Column(Integer, nullable=True)
    secret = Column(String(60), nullable=False)  # Secret partagé avec le NAS
    server = Column(String(64), nullable=True)
    community = Column(String(50), nullable=True)
    description = Column(String(200), nullable=True)
    
    def __repr__(self):
        return f"<NASInfo(nasname='{self.nasname}', shortname='{self.shortname}')>"
