from fastapi import APIRouter
from api.v1.endpoints import scans, devices, system

api_router = APIRouter()

# Unificamos todas las rutas bajo el prefijo /api
api_router.include_router(scans.router, tags=["scans"])
api_router.include_router(devices.router, tags=["devices"])
api_router.include_router(system.router, tags=["system"])
