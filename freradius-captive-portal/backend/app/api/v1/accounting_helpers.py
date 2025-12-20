"""
Fonctions helper pour la gestion des sessions d'accounting RADIUS
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.accounting import RadAcct

# Définition du type pour éviter l'importation circulaire
from typing import Any, Dict
# RadiusAccountingRequest sera passé comme paramètre

logger = logging.getLogger("radius_accounting")


async def _handle_accounting_start(request: Any, db: Session):
    """
    Gère le début d'une session utilisateur
    """
    try:
        # Vérifier si une session existe déjà pour cet utilisateur
        existing_session = db.query(RadAcct).filter(
            RadAcct.username == request.username,
            RadAcct.acctsessionid == request.session_id,
            RadAcct.acctstoptime.is_(None)
        ).first()
        
        if existing_session:
            logger.warning(f"Session already exists for user {request.username}, session {request.session_id}")
            return
        
        # Créer une nouvelle session avec nettoyage des champs vides
        new_session = RadAcct(
            acctsessionid=request.session_id,
            acctuniqueid=f"{request.session_id[:16]}-{int(datetime.now().timestamp())}",
            username=request.username,
            nasipaddress=request.nas_ip_address or "127.0.0.1",  # Valeur par défaut si None
            acctstarttime=datetime.now(),
            acctinputoctets=int(request.input_octets or 0),
            acctoutputoctets=int(request.output_octets or 0),
            framedipaddress=request.framed_ip_address if request.framed_ip_address and request.framed_ip_address.strip() else None,
            callingstationid=request.calling_station_id if request.calling_station_id and request.calling_station_id.strip() else None,
            calledstationid=request.called_station_id if request.called_station_id and request.called_station_id.strip() else None,
            acctterminatecause=request.terminate_cause if hasattr(request, 'terminate_cause') and request.terminate_cause and request.terminate_cause.strip() else None
        )
        
        db.add(new_session)
        db.commit()
        
        logger.info(f"Session started for user {request.username}, session {request.session_id}")
        
    except Exception as e:
        logger.error(f"Error starting session: {str(e)}", exc_info=True)
        db.rollback()
        raise


async def _handle_accounting_stop(request: Any, db: Session):
    """
    Gère la fin d'une session utilisateur
    """
    try:
        # Trouver la session active
        session = db.query(RadAcct).filter(
            RadAcct.username == request.username,
            RadAcct.acctsessionid == request.session_id,
            RadAcct.acctstoptime.is_(None)
        ).first()
        
        if not session:
            logger.warning(f"No active session found for user {request.username}, session {request.session_id}")
            return
        
        # Mettre à jour la session avec les données de fin
        session.acctstoptime = datetime.now()
        session.acctsessiontime = int(request.session_time or 0)
        session.acctinputoctets = int(request.input_octets or 0)
        session.acctoutputoctets = int(request.output_octets or 0)
        session.acctterminatecause = request.terminate_cause
        
        db.commit()
        
        # Calculer la durée de session
        duration = session.acctsessiontime or 0
        total_bytes = (session.acctinputoctets or 0) + (session.acctoutputoctets or 0)
        
        logger.info(
            f"Session stopped for user {request.username}, session {request.session_id}, "
            f"duration: {duration}s, total bytes: {total_bytes}"
        )
        
    except Exception as e:
        logger.error(f"Error stopping session: {str(e)}", exc_info=True)
        db.rollback()
        raise


async def _handle_accounting_update(request: Any, db: Session):
    """
    Gère les mises à jour intermédiaires d'une session
    """
    try:
        # Trouver la session active
        session = db.query(RadAcct).filter(
            RadAcct.username == request.username,
            RadAcct.acctsessionid == request.session_id,
            RadAcct.acctstoptime.is_(None)
        ).first()
        
        if not session:
            logger.warning(f"No active session found for update: user {request.username}, session {request.session_id}")
            return
        
        # Mettre à jour les statistiques
        session.acctupdatetime = datetime.now()
        session.acctinputoctets = int(request.input_octets or 0)
        session.acctoutputoctets = int(request.output_octets or 0)
        session.acctsessiontime = int(request.session_time or 0)
        
        db.commit()
        
        logger.debug(f"Session updated for user {request.username}, session {request.session_id}")
        
    except Exception as e:
        logger.error(f"Error updating session: {str(e)}", exc_info=True)
        db.rollback()
        raise
