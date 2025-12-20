from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import settings

# Connection à la base de données PostgreSQL configurée dans les variables d'environnement
DATABASE_URL = settings.DATABASE_URL

# Création du moteur SQLAlchemy
engine = create_engine(DATABASE_URL)

# Création d'une session locale pour les requêtes
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base de déclaration pour les modèles
Base = declarative_base()

# Fonction pour obtenir une session de base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
