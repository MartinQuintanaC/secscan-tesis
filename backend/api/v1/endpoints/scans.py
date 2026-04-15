from fastapi import APIRouter, HTTPException, Depends
from schemas.scan import ScanRequest, CVELookupRequest
from services.scan_service import ScanService
from services.db_service import DatabaseService
from api.deps import get_current_user
import requests

router = APIRouter()
scan_service = ScanService()
db_service = DatabaseService()

# Note: In a real modular setup, we'll use a global instance or dependency injection.
# For simplicity in this refactor, we instantiate the service.

@router.post("/discover")
def discover_network(request: ScanRequest, user: dict = Depends(get_current_user)):
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
def deep_scan_device(ip: str, user: dict = Depends(get_current_user)):
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
def trigger_scan(request: ScanRequest, user: dict = Depends(get_current_user)):
    """
    Intenta disparar n8n. Si n8n no está disponible, 
    ejecuta el escaneo completo directamente (Modo Directo).
    """
    n8n_disponible = False
    
    # Intentamos con n8n primero (Modo Turbo)
    url_prod = "http://localhost:5678/webhook/secscan"
    url_test = "http://localhost:5678/webhook-test/secscan"
    
    try:
        resp = requests.post(url_prod, json={"target_ip": request.target_ip}, timeout=2)
        if resp.status_code == 200:
            n8n_disponible = True
    except: pass
        
    if not n8n_disponible:
        try:
            resp = requests.post(url_test, json={"target_ip": request.target_ip}, timeout=2)
            if resp.status_code == 200:
                n8n_disponible = True
        except: pass
    
    if n8n_disponible:
        return {"status": "ok", "modo": "n8n", "mensaje": "Webhook disparado con éxito (Modo Turbo)"}
    
    # Si n8n no está disponible, escaneamos directamente (Modo Directo)
    print("⚠️ n8n no disponible. Activando Modo Directo de escaneo...")
    
    # Limpiamos datos anteriores para reflejar solo la red actual
    db_service.clear_devices()
    db_service.clear_vulnerabilities()
    
    result = scan_service.discover(request.target_ip)
    
    if result.get("error") == "NMAP_MISSING":
        return {"status": "error", "code": "NMAP_MISSING", "dispositivos": []}
    
    dispositivos = result.get("dispositivos", [])
    escaneados = 0
    
    for dispositivo in dispositivos:
        ip = dispositivo.get("ip", "")
        if ip:
            try:
                scan_service.deep_scan(ip)
                escaneados += 1
                print(f"✅ [{escaneados}/{len(dispositivos)}] Escaneado: {ip}")
            except Exception as e:
                print(f"❌ Error escaneando {ip}: {e}")
    
    return {
        "status": "ok", 
        "modo": "directo",
        "mensaje": f"Escaneo directo completado. {escaneados} dispositivos auditados.",
        "total_escaneados": escaneados
    }


@router.post("/cve-lookup")
def cve_lookup(request: CVELookupRequest, user: dict = Depends(get_current_user)):
    resultados = scan_service.cve_client.buscar_vulnerabilidades(request.servicio, request.version)
    return {
        "status": "ok",
        "servicio": request.servicio,
        "version": request.version,
        "total_cves": len(resultados),
        "vulnerabilidades": resultados
    }
