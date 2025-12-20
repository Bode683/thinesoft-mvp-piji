from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from config.settings import settings
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from app.database.db import get_db
from app.services.accounting_service import AccountingService
from app.models.accounting import RadAcct

# Configuration du logger
logger = logging.getLogger("radius_accounting")

# Import des fonctions helper
from .accounting_helpers import _handle_accounting_start, _handle_accounting_stop, _handle_accounting_update

router = APIRouter()

class RadiusAccountingRequest(BaseModel):
    username: str
    session_id: str
    status_type: str  # Start/Stop/Interim-Update
    input_octets: Optional[str] = "0"
    output_octets: Optional[str] = "0"
    input_packets: Optional[str] = "0"
    output_packets: Optional[str] = "0"
    session_time: Optional[str] = "0"
    nas_ip_address: Optional[str] = None
    nas_identifier: Optional[str] = None
    framed_ip_address: Optional[str] = None
    calling_station_id: Optional[str] = None  # MAC address
    called_station_id: Optional[str] = None   # AP MAC/SSID
    terminate_cause: Optional[str] = None

class UserAccounting(BaseModel):
    username: str
    session_id: str
    status_type: str  # start/stop/interim-update
    input_octets: Optional[int] = 0
    output_octets: Optional[int] = 0
    input_packets: Optional[int] = 0
    output_packets: Optional[int] = 0

def clean_request_data(request: RadiusAccountingRequest) -> RadiusAccountingRequest:
    """
    Nettoie les données de la requête en convertissant les chaînes vides en None
    pour éviter les erreurs PostgreSQL avec les types inet.
    """
    # Créer une copie des données de la requête
    data = request.dict()
    
    # Nettoyer les champs qui peuvent être des chaînes vides
    fields_to_clean = ['framed_ip_address', 'calling_station_id', 'called_station_id', 'nas_identifier', 'terminate_cause']
    
    for field in fields_to_clean:
        if field in data and data[field] == '':
            data[field] = None
    
    # Retourner un nouvel objet avec les données nettoyées
    return RadiusAccountingRequest(**data)

@router.post("/radius", tags=["Accounting"])
async def radius_accounting(request: RadiusAccountingRequest, db: Session = Depends(get_db)):
    """
    Endpoint principal pour l'accounting RADIUS appelé par FreeRADIUS.
    Gère les événements Start, Stop et Interim-Update.
    
    Args:
        request: Données d'accounting RADIUS
        db: Session de base de données
    
    Returns:
        Confirmation du traitement
    """
    try:
        # Nettoyer les données de la requête
        cleaned_request = clean_request_data(request)
        
        status_type = cleaned_request.status_type
        username = cleaned_request.username
        session_id = cleaned_request.session_id
        nas_ip = cleaned_request.nas_ip_address or "unknown"
        
        logger.info(f"RADIUS ACCOUNTING: {status_type} for user {username}, session {session_id}, NAS {nas_ip}")
        
        if status_type == "Start":
            # Début de session
            await _handle_accounting_start(cleaned_request, db)
            
        elif status_type == "Stop":
            # Fin de session
            await _handle_accounting_stop(cleaned_request, db)
            
        elif status_type == "Interim-Update":
            # Mise à jour intermédiaire
            await _handle_accounting_update(cleaned_request, db)
            
        elif status_type == "Post-Auth":
            # Post-authentification - ne nécessite pas d'action spécifique en base
            # C'est une notification envoyée par FreeRADIUS après une authentification réussie
            logger.info(f"RADIUS POST-AUTH: Session notification pour {username} depuis {nas_ip}")
            
        else:
            logger.warning(f"Unknown accounting status type: {status_type}")
            
        return {
            "status": "success",
            "message": f"Accounting {status_type} processed for user {username}"
        }
        
    except Exception as e:
        logger.error(f"ACCOUNTING ERROR: User={request.username}, Error={str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": "Accounting processing failed",
            "error": str(e)
        }

@router.post("/accounting", tags=["Accounting"])
async def accounting(user: UserAccounting):
    """
    Endpoint legacy pour compatibilité avec le portail captif
    
    Args:
        user: Données d'accounting simplifiées
    
    Returns:
        Dictionnaire contenant le statut de l'accounting
    """
    try:
        logger.info(f"LEGACY ACCOUNTING: {user.status_type} for user {user.username}, session {user.session_id}")
        
        # Convertir vers le format RADIUS
        radius_request = RadiusAccountingRequest(
            username=user.username,
            session_id=user.session_id,
            status_type=user.status_type.title(),  # Convertir en format RADIUS
            input_octets=str(user.input_octets),
            output_octets=str(user.output_octets),
            input_packets=str(user.input_packets),
            output_packets=str(user.output_packets)
        )
        
        # Utiliser l'endpoint principal
        from app.database.db import get_db
        db = next(get_db())
        try:
            result = await radius_accounting(radius_request, db)
            return result
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"LEGACY ACCOUNTING ERROR: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.get("/active-sessions/", tags=["Accounting"], response_model=List[Dict[str, Any]])
def get_active_sessions(db: Session = Depends(get_db)):
    """
    Récupère toutes les sessions utilisateur actuellement actives.
    
    Returns:
        Liste des sessions actives avec détails utilisateur et point d'accès
    """
    try:
        active_sessions = AccountingService.get_active_sessions(db)
        result = []
        
        for session in active_sessions:
            result.append({
                "username": session.username,
                "acctsessionid": session.acctsessionid,
                "acctuniqueid": session.acctuniqueid,
                "nasipaddress": session.nasipaddress,
                "callingstationid": session.callingstationid,  # MAC address
                "framedipaddress": session.framedipaddress,     # IP address
                "acctstarttime": session.acctstarttime,
                "duration_seconds": session.duration_seconds,
                "input_octets": session.acctinputoctets or 0,
                "output_octets": session.acctoutputoctets or 0,
                "total_octets": session.total_octets,
                "total_mb": session.total_megabytes
            })
            
        return result
    except Exception as e:
        error_details = {"error": str(e)}
        raise HTTPException(status_code=500, detail=error_details)


@router.get("/bandwidth-stats/", tags=["Accounting"])
def get_global_bandwidth_stats(
    period_days: int = Query(30, description="Période en jours pour les statistiques"),
    db: Session = Depends(get_db)
):
    """
    Récupère les statistiques globales d'utilisation de la bande passante.
    
    Args:
        period_days: Période en jours à considérer (défaut: 30)
        
    Returns:
        Statistiques globales de bande passante et d'utilisateurs
    """
    try:
        stats = AccountingService.get_global_bandwidth_usage(db, period_days)
        # Ajoute la date actuelle aux statistiques
        stats["timestamp"] = datetime.utcnow().isoformat()
        return stats
    except Exception as e:
        error_details = {"error": str(e)}
        raise HTTPException(status_code=500, detail=error_details)


@router.get("/user-bandwidth/{username}", tags=["Accounting"])
def get_user_bandwidth_stats(
    username: str,
    period_days: int = Query(30, description="Période en jours pour les statistiques"),
    db: Session = Depends(get_db)
):
    """
    Récupère les statistiques d'utilisation de la bande passante pour un utilisateur spécifique.
    
    Args:
        username: Nom d'utilisateur
        period_days: Période en jours à considérer (défaut: 30)
        
    Returns:
        Statistiques détaillées de bande passante pour l'utilisateur
    """
    try:
        stats = AccountingService.get_user_bandwidth_usage(db, username, period_days)
        # Récupère également les sessions actives de l'utilisateur
        active_sessions = AccountingService.get_user_sessions(db, username, active_only=True)
        
        # Ajoute les détails des sessions actives aux statistiques
        stats["active_sessions"] = [{
            "acctsessionid": session.acctsessionid,
            "nasipaddress": session.nasipaddress,
            "framedipaddress": session.framedipaddress,
            "acctstarttime": session.acctstarttime.isoformat() if session.acctstarttime else None,
            "duration_seconds": session.duration_seconds,
            "total_mb": session.total_megabytes
        } for session in active_sessions]
        
        return stats
    except Exception as e:
        error_details = {"error": str(e)}
        raise HTTPException(status_code=500, detail=error_details)


@router.get("/daily-stats/", tags=["Accounting"])
def get_daily_bandwidth_stats(
    days: int = Query(30, description="Nombre de jours d'historique à récupérer"),
    db: Session = Depends(get_db)
):
    """
    Récupère l'historique quotidien d'utilisation de la bande passante.
    Utile pour les graphiques d'évolution dans le dashboard administrateur.
    
    Args:
        days: Nombre de jours d'historique à récupérer (défaut: 30)
        
    Returns:
        Liste des utilisations quotidiennes de bande passante
    """
    try:
        daily_stats = AccountingService.get_daily_bandwidth_usage(db, days)
        return daily_stats
    except Exception as e:
        error_details = {"error": str(e)}
        raise HTTPException(status_code=500, detail=error_details)


@router.get("/top-users/", tags=["Accounting"])
def get_top_bandwidth_users(
    limit: int = Query(10, description="Nombre d'utilisateurs à récupérer"),
    period_days: int = Query(30, description="Période en jours à considérer"),
    db: Session = Depends(get_db)
):
    """
    Récupère les utilisateurs les plus consommateurs de bande passante.
    
    Args:
        limit: Nombre maximum d'utilisateurs à retourner (défaut: 10)
        period_days: Période en jours à considérer (défaut: 30)
        
    Returns:
        Liste des top utilisateurs avec leur consommation de bande passante
    """
    try:
        top_users = AccountingService.get_top_users_by_bandwidth(db, limit, period_days)
        return top_users
    except Exception as e:
        error_details = {"error": str(e)}
        raise HTTPException(status_code=500, detail=error_details)


@router.get("/nas-list/", tags=["Accounting"])
def get_nas_info(db: Session = Depends(get_db)):
    """
    Récupère la liste des points d'accès (NAS) enregistrés.
    
    Returns:
        Liste des points d'accès avec leurs détails
    """
    try:
        nas_list = AccountingService.get_nas_info(db)
        return [{
            "id": nas.id,
            "nasname": nas.nasname,
            "shortname": nas.shortname,
            "type": nas.type,
            "description": nas.description,
            # Ne pas inclure le secret pour des raisons de sécurité
        } for nas in nas_list]
    except Exception as e:
        error_details = {"error": str(e)}
        raise HTTPException(status_code=500, detail=error_details)
