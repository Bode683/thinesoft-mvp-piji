from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings

app = FastAPI(
    title="WiFi Hotspot Management API",
    description="API pour la gestion des hotspots WiFi avec FreeRADIUS",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation des routes
from app.api import init_routers
init_routers(app)
