from fastapi import APIRouter
from api.v1.endpoints import scans, devices, system

api_router = APIRouter()

# Unificamos todas las rutas bajo el prefijo /api
api_router.include_router(scans.router, tags=["scans"])
api_router.include_router(devices.router, tags=["devices"])
api_router.include_router(system.router, tags=["system"])

# ========== RUTAS INTERNAS PARA N8N (Sin Auth) ==========
from services.scan_service import ScanService
from services.db_service import DatabaseService
from schemas.scan import ScanRequest

n8n_router = APIRouter()
_scan_service = ScanService()
_db_service = DatabaseService()

@n8n_router.post("/discover")
def n8n_discover(request: ScanRequest):
    """Ruta interna para que n8n descubra dispositivos sin necesitar JWT."""
    # Limpiamos el estado anterior para reflejar solo la red actual
    _db_service.clear_devices()
    _db_service.clear_vulnerabilities()
    
    result = _scan_service.discover(request.target_ip)
    if result.get("error") == "NMAP_MISSING":
        return {"status": "error", "code": "NMAP_MISSING", "dispositivos": []}
    return {
        "status": "ok", 
        "total": len(result["dispositivos"]),
        "dispositivos": result["dispositivos"]
    }

@n8n_router.post("/deep-scan/{ip}")
def n8n_deep_scan(ip: str):
    """Ruta interna para que n8n escanee un dispositivo sin necesitar JWT."""
    detalle = _scan_service.deep_scan(ip)
    return {
        "status": "ok",
        "ip_escaneada": ip,
        "puertos_encontrados": len(detalle.get("puertos_abiertos", [])),
        "vulnerabilidades_encontradas": detalle.get("total_vulnerabilidades", 0),
        "detalle": detalle
    }
