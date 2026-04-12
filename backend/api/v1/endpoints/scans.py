from fastapi import APIRouter, HTTPException
from schemas.scan import ScanRequest, CVELookupRequest
from services.scan_service import ScanService
import requests

router = APIRouter()
scan_service = ScanService()

@app_router_instance_placeholder
# Note: In a real modular setup, we'll use a global instance or dependency injection.
# For simplicity in this refactor, we instantiate the service.

@router.post("/discover")
def discover_network(request: ScanRequest):
    result = scan_service.discover(request.target_ip)
    if result.get("error") == "NMAP_MISSING":
        return {
            "status": "error", 
            "code": "NMAP_MISSING", 
            "dispositivos": []
        }
    
    return {
        "status": "ok", 
        "total": len(result["dispositivos"]),
        "dispositivos": result["dispositivos"]
    }

@router.post("/deep-scan/{ip}")
def deep_scan_device(ip: str):
    try:
        detalle = scan_service.deep_scan(ip)
        return {
            "status": "ok",
            "ip_escaneada": ip,
            "puertos_encontrados": len(detalle.get("puertos_abiertos", [])),
            "vulnerabilidades_encontradas": detalle.get("total_vulnerabilidades", 0),
            "detalle": detalle
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger-scan")
def trigger_scan(request: ScanRequest):
    url_prod = "http://localhost:5678/webhook/secscan"
    url_test = "http://localhost:5678/webhook-test/secscan"
    
    try:
        requests.post(url_prod, json={"target_ip": request.target_ip}, timeout=1)
    except: pass
        
    try:
        requests.post(url_test, json={"target_ip": request.target_ip}, timeout=1)
    except: pass
        
    return {"status": "ok", "mensaje": "Webhook disparado con éxito"}

@router.post("/cve-lookup")
def cve_lookup(request: CVELookupRequest):
    resultados = scan_service.cve_client.buscar_vulnerabilidades(request.servicio, request.version)
    return {
        "status": "ok",
        "servicio": request.servicio,
        "version": request.version,
        "total_cves": len(resultados),
        "vulnerabilidades": resultados
    }
