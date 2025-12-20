from fastapi import FastAPI
from .v1 import auth, accounting


def init_routers(app: FastAPI):
    """
    Initialise les routes de l'API
    """
    app.include_router(auth.router, prefix="/api/v1/auth")
    app.include_router(accounting.router, prefix="/api/v1/accounting")
