from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from app.models.accounting import RadAcct, NASInfo
from app.models.radius import RadCheck

class AccountingService:
    """
    Service pour accéder aux données d'accounting de FreeRADIUS.
    Fournit des méthodes pour récupérer les statistiques de bande passante,
    les sessions actives, et l'historique des connexions.
    """
    
    @staticmethod
    def get_active_sessions(db: Session) -> List[RadAcct]:
        """
        Récupère toutes les sessions actives (non terminées).
        
        Args:
            db: Session de base de données
            
        Returns:
            Liste des sessions actives
        """
        return db.query(RadAcct).filter(
            RadAcct.acctstoptime == None
        ).order_by(desc(RadAcct.acctstarttime)).all()
    
    @staticmethod
    def get_user_sessions(db: Session, username: str, active_only: bool = False) -> List[RadAcct]:
        """
        Récupère les sessions d'un utilisateur spécifique.
        
        Args:
            db: Session de base de données
            username: Nom d'utilisateur
            active_only: Si True, ne récupère que les sessions actives
            
        Returns:
            Liste des sessions de l'utilisateur
        """
        query = db.query(RadAcct).filter(RadAcct.username == username)
        
        if active_only:
            query = query.filter(RadAcct.acctstoptime == None)
            
        return query.order_by(desc(RadAcct.acctstarttime)).all()
    
    @staticmethod
    def get_user_bandwidth_usage(db: Session, username: str, period_days: int = 30) -> Dict[str, Any]:
        """
        Calcule l'utilisation de bande passante pour un utilisateur sur une période donnée.
        
        Args:
            db: Session de base de données
            username: Nom d'utilisateur
            period_days: Nombre de jours à considérer (par défaut 30)
            
        Returns:
            Dictionnaire avec les statistiques d'utilisation
        """
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Sélectionne les sessions dans la période spécifiée
        sessions = db.query(RadAcct).filter(
            and_(
                RadAcct.username == username,
                RadAcct.acctstarttime >= start_date
            )
        ).all()
        
        # Calcul des totaux
        download_total = sum(s.acctinputoctets or 0 for s in sessions)
        upload_total = sum(s.acctoutputoctets or 0 for s in sessions)
        total_octets = download_total + upload_total
        
        # Convertit en formats plus lisibles
        download_mb = round(download_total / (1024 * 1024), 2)
        upload_mb = round(upload_total / (1024 * 1024), 2)
        total_mb = round(total_octets / (1024 * 1024), 2)
        total_gb = round(total_octets / (1024 * 1024 * 1024), 2)
        
        # Temps total de connexion en secondes
        total_time = sum(s.duration_seconds for s in sessions)
        
        return {
            "username": username,
            "period_days": period_days,
            "download_octets": download_total,
            "upload_octets": upload_total,
            "total_octets": total_octets,
            "download_mb": download_mb,
            "upload_mb": upload_mb,
            "total_mb": total_mb,
            "total_gb": total_gb,
            "total_time_seconds": total_time,
            "total_time_hours": round(total_time / 3600, 1),
            "session_count": len(sessions)
        }
    
    @staticmethod
    def get_global_bandwidth_usage(db: Session, period_days: int = 30) -> Dict[str, Any]:
        """
        Calcule l'utilisation de bande passante globale sur une période donnée.
        
        Args:
            db: Session de base de données
            period_days: Nombre de jours à considérer (par défaut 30)
            
        Returns:
            Dictionnaire avec les statistiques d'utilisation globales
        """
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Sélectionne les sessions dans la période spécifiée
        result = db.query(
            func.sum(RadAcct.acctinputoctets).label("download_total"),
            func.sum(RadAcct.acctoutputoctets).label("upload_total"),
            func.count(RadAcct.radacctid).label("session_count")
        ).filter(
            RadAcct.acctstarttime >= start_date
        ).first()
        
        download_total = result.download_total or 0
        upload_total = result.upload_total or 0
        total_octets = download_total + upload_total
        session_count = result.session_count or 0
        
        # Active users count (distinct usernames with active sessions)
        active_users_count = db.query(
            func.count(func.distinct(RadAcct.username))
        ).filter(
            RadAcct.acctstoptime == None
        ).scalar() or 0
        
        # Total registered users
        total_users_count = db.query(
            func.count(func.distinct(RadCheck.username))
        ).scalar() or 0
        
        return {
            "period_days": period_days,
            "download_octets": download_total,
            "upload_octets": upload_total,
            "total_octets": total_octets,
            "download_gb": round(download_total / (1024 * 1024 * 1024), 2),
            "upload_gb": round(upload_total / (1024 * 1024 * 1024), 2),
            "total_gb": round(total_octets / (1024 * 1024 * 1024), 2),
            "session_count": session_count,
            "active_users_count": active_users_count,
            "total_users_count": total_users_count
        }
    
    @staticmethod
    def get_daily_bandwidth_usage(db: Session, days: int = 30) -> List[Dict[str, Any]]:
        """
        Récupère l'utilisation quotidienne de bande passante sur une période donnée.
        Utile pour les graphiques d'évolution.
        
        Args:
            db: Session de base de données
            days: Nombre de jours à considérer
            
        Returns:
            Liste des utilisations quotidiennes
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        daily_usage = []
        
        for day_offset in range(days):
            day_date = start_date + timedelta(days=day_offset)
            next_day = day_date + timedelta(days=1)
            
            # Sessions commencées ou actives ce jour-là
            result = db.query(
                func.sum(RadAcct.acctinputoctets).label("download"),
                func.sum(RadAcct.acctoutputoctets).label("upload")
            ).filter(
                and_(
                    RadAcct.acctstarttime < next_day,
                    or_(
                        RadAcct.acctstoptime >= day_date,
                        RadAcct.acctstoptime == None
                    )
                )
            ).first()
            
            download = result.download or 0
            upload = result.upload or 0
            
            daily_usage.append({
                "date": day_date.strftime("%Y-%m-%d"),
                "download_mb": round(download / (1024 * 1024), 2),
                "upload_mb": round(upload / (1024 * 1024), 2),
                "total_mb": round((download + upload) / (1024 * 1024), 2)
            })
        
        return daily_usage
    
    @staticmethod
    def get_nas_info(db: Session, nasname: Optional[str] = None) -> List[NASInfo]:
        """
        Récupère les informations sur les points d'accès (NAS).
        
        Args:
            db: Session de base de données
            nasname: Si fourni, filtre sur ce NAS spécifique
            
        Returns:
            Liste des points d'accès
        """
        query = db.query(NASInfo)
        
        if nasname:
            query = query.filter(NASInfo.nasname == nasname)
            
        return query.all()
    
    @staticmethod
    def get_top_users_by_bandwidth(db: Session, limit: int = 10, period_days: int = 30) -> List[Dict[str, Any]]:
        """
        Récupère les utilisateurs les plus consommateurs de bande passante.
        
        Args:
            db: Session de base de données
            limit: Nombre maximum d'utilisateurs à retourner
            period_days: Période à considérer en jours
            
        Returns:
            Liste des top utilisateurs avec leur consommation
        """
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Agrégation par username
        results = db.query(
            RadAcct.username,
            func.sum(RadAcct.acctinputoctets).label("download"),
            func.sum(RadAcct.acctoutputoctets).label("upload"),
            func.sum(RadAcct.acctsessiontime).label("total_time")
        ).filter(
            and_(
                RadAcct.username != None,
                RadAcct.acctstarttime >= start_date
            )
        ).group_by(
            RadAcct.username
        ).order_by(
            func.sum(RadAcct.acctinputoctets + RadAcct.acctoutputoctets).desc()
        ).limit(limit).all()
        
        top_users = []
        for row in results:
            download = row.download or 0
            upload = row.upload or 0
            total = download + upload
            
            top_users.append({
                "username": row.username,
                "download_mb": round(download / (1024 * 1024), 2),
                "upload_mb": round(upload / (1024 * 1024), 2),
                "total_mb": round(total / (1024 * 1024), 2),
                "total_gb": round(total / (1024 * 1024 * 1024), 2),
                "total_time_hours": round((row.total_time or 0) / 3600, 1)
            })
        
        return top_users
