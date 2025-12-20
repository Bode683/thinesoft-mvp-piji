from fastapi import APIRouter, HTTPException, Depends, Response, status
from pydantic import BaseModel
from config.settings import settings
import logging
import datetime
from typing import Optional, Dict, Any, Union, List

# Configuration du logger
import os

# Chemin des logs dans le volume monté sur Docker
log_dir = "/app/logs"
try:
    # S'assurer que le répertoire existe (devrait déjà exister grâce au volume)
    os.makedirs(log_dir, exist_ok=True)
    print(f"Répertoire de logs créé ou vérifié: {log_dir}")
except Exception as e:
    print(f"Avertissement: Impossible de créer le répertoire de logs {log_dir}: {e}")

# Configuration du logger avec gestion d'erreurs
handlers = [logging.StreamHandler()]  # Logs vers console toujours disponible

try:
    # Essayer d'ajouter le fichier de log au chemin monté
    log_file = os.path.join(log_dir, "radius_auth.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    handlers.append(file_handler)
    print(f"Handler de fichier log créé avec succès: {log_file}")
except Exception as e:
    print(f"Avertissement: Impossible de créer le fichier de logs {log_file}: {e}")

logging.basicConfig(
    level=logging.DEBUG,  # Niveau de détail maximum pour le développement
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger("radius_auth")

router = APIRouter()

# Modèle pour les requêtes d'authentification
# Ce modèle doit correspondre exactement à la façon dont rlm_rest envoie les données
class UserAuth(BaseModel):
    username: str
    password: str
    nas_ip_address: Optional[str] = None
    nas_identifier: Optional[str] = None
    service_type: Optional[str] = None

class AccountingRequest(BaseModel):
    username: str
    session_id: str
    status_type: str
    nas_ip_address: Optional[str] = None
    input_octets: Optional[str] = None
    output_octets: Optional[str] = None
    input_packets: Optional[str] = None
    output_packets: Optional[str] = None
    session_time: Optional[str] = None
    
class PostAuthRequest(BaseModel):
    username: str
    result: str
    nas_ip_address: Optional[str] = None

from app.database.db import get_db
from app.models.radius import RadCheck, RadReply, RadUserGroup, RadGroupReply
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Sécurité des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schémas de requête et réponse pour les opérations sur les utilisateurs
class UserCreate(BaseModel):
    username: str
    password: str
    group: Optional[str] = "users"
    attributes: Optional[Dict[str, str]] = None

class UserResponse(BaseModel):
    username: str
    attributes: Dict[str, str] = {}
    groups: list = []
    
    class Config:
        orm_mode = True

class UserListResponse(BaseModel):
    users: List[UserResponse]
    count: int

def verify_password(plain_password: str, password_value: str) -> bool:
    """Vérifie si le mot de passe en texte brut correspond à celui stocké dans la base RADIUS.
    
    Dans une base FreeRADIUS typique, les mots de passe peuvent être stockés de plusieurs façons:
    - Cleartext-Password : texte brut
    - MD5-Password, SHA-Password, etc. : formats hashés
    """
    # Pour Cleartext-Password, on fait une simple comparaison
    # Pour les autres formats, on utiliserait des algorithmes spécifiques
    return plain_password == password_value

def get_user_password(db: Session, username: str) -> Optional[str]:
    """Récupère le mot de passe d'un utilisateur depuis la table radcheck."""
    # Recherche du mot de passe dans radcheck (généralement avec attribute='Cleartext-Password')
    password_check = db.query(RadCheck).filter(
        RadCheck.username == username,
        RadCheck.attribute.in_(['Cleartext-Password', 'Password', 'User-Password'])
    ).first()
    
    if password_check:
        return password_check.value
    return None

def get_user_attributes(db: Session, username: str) -> Dict[str, str]:
    """Récupère tous les attributs de réponse pour un utilisateur."""
    # Attributs directs de l'utilisateur
    user_replies = db.query(RadReply).filter(RadReply.username == username).all()
    
    # Attributs via les groupes de l'utilisateur
    user_groups = db.query(RadUserGroup).filter(RadUserGroup.username == username).all()
    group_names = [ug.groupname for ug in user_groups]
    
    group_replies = db.query(RadGroupReply).filter(
        RadGroupReply.groupname.in_(group_names)
    ).all() if group_names else []
    
    # Assemblage des attributs
    attributes = {}
    
    # Attributs utilisateur directs
    for reply in user_replies:
        attributes[reply.attribute] = reply.value
    
    # Attributs des groupes (les attributs utilisateur ont priorité)
    for greply in group_replies:
        if greply.attribute not in attributes:
            attributes[greply.attribute] = greply.value
    
    return attributes

@router.post("/radius", tags=["Authentication"])
async def authenticate_user(user: UserAuth, db: Session = Depends(get_db)):
    """
    Endpoint d'authentification utilisé par le module rlm_rest de FreeRADIUS.
    
    Cette fonction consulte la base de données FreeRADIUS existante pour authentifier
    l'utilisateur et récupérer ses attributs.
    
    Args:
        user: Informations d'authentification (username, password)
        db: Session de base de données
        
    Returns:
        Un objet JSON au format attendu par rlm_rest
    """
    try:
        # Journalisation détaillée de la tentative d'authentification
        source_ip = user.nas_ip_address or "unknown"
        nas_id = user.nas_identifier or "unknown"
        logger.info(f"RADIUS AUTH REQUEST: User={user.username} from NAS-IP={source_ip} NAS-ID={nas_id}")
        
        # Vérifier si le nom d'utilisateur est fourni
        if not user.username:
            logger.warning("RADIUS AUTH FAILURE: Username not provided")
            return {
                "control:Auth-Type": "Reject",
                "reply:Reply-Message": "Username is required"
            }
        
        # Récupération du mot de passe dans la base
        stored_password = get_user_password(db, user.username)
        
        # Si l'utilisateur n'existe pas
        if not stored_password:
            logger.warning(f"RADIUS AUTH FAILURE: User '{user.username}' not found")
            return {
                "control:Auth-Type": "Reject",
                "reply:Reply-Message": "User not found"
            }
        
        # Vérification du mot de passe
        if verify_password(user.password, stored_password):
            # Authentification réussie
            logger.info(f"RADIUS AUTH SUCCESS: User={user.username} authenticated successfully")
            
            # Récupération des attributs de l'utilisateur
            attributes = get_user_attributes(db, user.username)
            
            # Construction de la réponse pour FreeRADIUS
            response = {
                "control:Auth-Type": "Accept",
                "reply:Reply-Message": f"Hello {user.username}, authentication successful"
            }
            
            # Ajout des attributs spécifiques à l'utilisateur
            for attr_name, attr_value in attributes.items():
                response[f"reply:{attr_name}"] = attr_value
            
            # Si aucun attribut n'a été défini, ajoutons des attributs par défaut
            if not attributes:
                response["reply:Service-Type"] = "Framed-User"
                response["reply:Framed-IP-Address"] = "10.0.0.100"
                response["reply:Session-Timeout"] = "3600"
            
            # Ajouter des attributs couramment utilisés pour RADIUS
            if "Service-Type" not in attributes:
                response["reply:Service-Type"] = "Framed-User"
                
            # Log complet des attributs renvoyés
            logger.debug(f"RADIUS AUTH ATTRIBUTES: User={user.username}, Attributes={response}")
            
            return response
            
        else:
            # Authentification échouée - mot de passe incorrect
            logger.warning(f"RADIUS AUTH FAILURE: Invalid password for user={user.username}")
            
            return {
                "control:Auth-Type": "Reject",
                "reply:Reply-Message": "Invalid username or password"
            }
            
    except Exception as e:
        # Log d'erreur détaillé
        logger.error(f"RADIUS AUTH ERROR: User={user.username}, Error={str(e)}", exc_info=True)
        
        return {
            "control:Auth-Type": "Reject",
            "reply:Reply-Message": "Authentication server error"
        }

@router.get("/users", response_model=UserListResponse, tags=["User Management"])
async def get_all_users(db: Session = Depends(get_db)):
    """
    Récupère la liste de tous les utilisateurs FreeRADIUS.
    """
    try:
        # Récupérer les utilisateurs uniques depuis radcheck
        users_query = db.query(RadCheck.username).distinct().all()
        usernames = [u.username for u in users_query]
        
        # Pour chaque utilisateur, récupérer ses attributs et groupes
        user_list = []
        for username in usernames:
            # Attributs de l'utilisateur
            attributes = get_user_attributes(db, username)
            
            # Groupes de l'utilisateur
            user_groups = db.query(RadUserGroup).filter(RadUserGroup.username == username).all()
            groups = [ug.groupname for ug in user_groups]
            
            user_list.append(UserResponse(
                username=username,
                attributes=attributes,
                groups=groups
            ))
        
        return UserListResponse(users=user_list, count=len(user_list))
    
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")

@router.get("/users/{username}", response_model=UserResponse, tags=["User Management"])
async def get_user(username: str, db: Session = Depends(get_db)):
    """
    Récupère les détails d'un utilisateur spécifique.
    """
    try:
        # Vérifier si l'utilisateur existe
        user_check = db.query(RadCheck).filter(RadCheck.username == username).first()
        
        if not user_check:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")
        
        # Récupérer les attributs et groupes de l'utilisateur
        attributes = get_user_attributes(db, username)
        user_groups = db.query(RadUserGroup).filter(RadUserGroup.username == username).all()
        groups = [ug.groupname for ug in user_groups]
        
        return UserResponse(
            username=username,
            attributes=attributes,
            groups=groups
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user: {str(e)}")

@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserResponse, tags=["User Management"])
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Crée un nouvel utilisateur FreeRADIUS.
    """
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = db.query(RadCheck).filter(RadCheck.username == user.username).first()
        
        if existing_user:
            raise HTTPException(status_code=409, detail=f"User '{user.username}' already exists")
        
        # Créer l'enregistrement de mot de passe
        password_check = RadCheck(
            username=user.username,
            attribute="Cleartext-Password",  # Utiliser le format approprié selon votre configuration
            op=":=",
            value=user.password
        )
        db.add(password_check)
        
        # Ajouter l'utilisateur au groupe spécifié
        if user.group:
            user_group = RadUserGroup(
                username=user.username,
                groupname=user.group,
                priority=1
            )
            db.add(user_group)
        
        # Ajouter les attributs spécifiques si fournis
        if user.attributes:
            for attr_name, attr_value in user.attributes.items():
                reply = RadReply(
                    username=user.username,
                    attribute=attr_name,
                    op="=",
                    value=attr_value
                )
                db.add(reply)
        
        # Valider les changements
        db.commit()
        
        # Récupérer et retourner l'utilisateur créé
        return await get_user(user.username, db)
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user {user.username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT, tags=["User Management"])
async def delete_user(username: str, db: Session = Depends(get_db)):
    """
    Supprime un utilisateur FreeRADIUS et tous ses attributs associés.
    """
    try:
        # Vérifier si l'utilisateur existe
        user_check = db.query(RadCheck).filter(RadCheck.username == username).first()
        
        if not user_check:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")
        
        # Supprimer toutes les entrées liées à cet utilisateur
        db.query(RadCheck).filter(RadCheck.username == username).delete()
        db.query(RadReply).filter(RadReply.username == username).delete()
        db.query(RadUserGroup).filter(RadUserGroup.username == username).delete()
        
        # Valider les changements
        db.commit()
        
        return None
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user {username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


@router.get("/health", tags=["System"])
async def health_check():
    """
    Endpoint de vérification de l'état du service.
    Utilisé par FreeRADIUS pour tester la connectivité avec l'API.
    """
    try:
        # Journaliser l'appel au health check
        logger.debug("Health check request received")
        
        # Créer une réponse avec l'heure actuelle
        response = {
            "status": "ok",
            "timestamp": datetime.datetime.now().isoformat(),
            "service": "radius_auth_api"
        }
        
        return response
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Health check failed")

@router.post("/health", tags=["System"])
async def health_check_post():
    """Endpoint de vérification santé accessible en POST pour compatibilité FreeRADIUS"""
    return await health_check()


@router.post("/post-auth", tags=["Authentication"])
async def post_auth(request: PostAuthRequest):
    """
    Endpoint pour le traitement post-authentification.
    Appelé par FreeRADIUS après une tentative d'authentification (réussie ou échouée).
    
    Args:
        request: Informations sur l'authentification (username, result, nas_ip_address)
    
    Returns:
        Un message de confirmation
    """
    try:
        # Journalisation détaillée
        source_ip = request.nas_ip_address or "unknown"
        result = request.result
        logger.info(f"RADIUS POST-AUTH: User={request.username}, Result={result}, NAS={source_ip}")
        
        # Traitement supplémentaire peut être ajouté ici (statistiques, notifications, etc.)
        
        return {
            "status": "success",
            "message": f"Post-auth processed for user {request.username}"
        }
    
    except Exception as e:
        logger.error(f"POST-AUTH ERROR: User={request.username}, Error={str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": "Post-auth processing failed"
        }


@router.get("/radius", tags=["Authentication"])
async def authenticate_user_get(username: str, password: str, nas_ip_address: Optional[str] = None, nas_identifier: Optional[str] = None, service_type: Optional[str] = None, db: Session = Depends(get_db)):
    """Version GET pour compatibilité rlm_rest (au cas où la méthode serait GET)."""
    user = UserAuth(
        username=username,
        password=password,
        nas_ip_address=nas_ip_address,
        nas_identifier=nas_identifier,
        service_type=service_type,
    )
    return await authenticate_user(user, db)

# Endpoint d'accounting supprimé - maintenant géré dans accounting.py
# pour éviter les doublons et améliorer la séparation des responsabilités
