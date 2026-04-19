from fastapi import APIRouter, HTTPException, Depends, Header
from schemas.scan import ScanRequest, CVELookupRequest
from services.scan_service import ScanService
from services.db_service import DatabaseService
from api.deps import get_current_user
import requests
import uuid
import os

router = APIRouter()
scan_service = ScanService()
db_service = DatabaseService()

# API Key interna para proteger /internal/*
INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY", "secscan-internal-key-2024")

def verify_internal_key(x_internal_key: str = Header(None)):
    """Verifica que la request viene de n8n (no de outside)."""
    if x_internal_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid internal key")
    return True


@router.post("/discover")
def discover_network(request: ScanRequest, user: dict = Depends(get_current_user)):
    user_id = user.get("uid", "")
    result = scan_service.discover(request.target_ip)
    if result.get("error") == "NMAP_MISSING":
        return {"status": "error", "code": "NMAP_MISSING", "dispositivos": []}
    
    return {
        "status": "ok", 
        "total": len(result["dispositivos"]),
        "dispositivos": result["dispositivos"],
        "user_id": user_id
    }


@router.post("/deep-scan/{ip}")
def deep_scan_device(ip: str, user: dict = Depends(get_current_user)):
    user_id = user.get("uid", "")
    try:
        detalle = scan_service.deep_scan(ip, user_id)
        return {
            "status": "ok",
            "ip_escaneada": ip,
            "user_id": user_id,
            "puertos_encontrados": len(detalle.get("puertos_abiertos", [])),
            "vulnerabilidades_encontradas": detalle.get("total_vulnerabilidades", 0),
            "detalle": detalle
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-scan")
def trigger_scan(request: ScanRequest, authorization: str = Header(None), user: dict = Depends(get_current_user)):
    """
    Endpoint BFF (Backend-for-Frontend) - Versión Segura.
    - Valida JWT
    - Genera scanId único (idempotencia)
    - Pasa token REAL a n8n para validación interna
    """
    # 1. Extraer uid del token JWT (FUENTE DE VERDAD)
    user_id = user.get("uid", "")
    target_ip = request.target_ip if request.target_ip else "auto"
    
    # 2. Usar scanId del frontend o generar uno nuevo (Idempotencia)
    scan_id = request.scan_id if request.scan_id else str(uuid.uuid4())
    
    # 3. Extraer el token puro (sin 'Bearer ')
    raw_token = authorization.split(" ")[1] if authorization and "Bearer" in authorization else ""

    print(f"🚀 [BFF] Iniciando Escaneo Global")
    print(f"👤 Usuario: {user_id}")
    print(f"🆔 ScanId: {scan_id}")
    
    # 4. Limpiar datos anteriores del usuario (opcional si usas subcolecciones por scan)
    db_service.clear_devices(user_id)
    db_service.clear_vulnerabilities(user_id)
    
    # 5. Preparar payload para n8n (CON TOKEN REAL)
    payload = {
        "target_ip": target_ip,
        "token": raw_token,
        "scan_id": scan_id,
        "user_id": user_id 
    }

    
    # 5. Llamar a n8n
    n8n_disponible = False
    url_prod = "http://localhost:5678/webhook/secscan"
    url_test = "http://localhost:5678/webhook-test/secscan"
    
    try:
        resp = requests.post(url_prod, json=payload, timeout=2)
        if resp.status_code == 200:
            n8n_disponible = True
    except: pass
            
    if not n8n_disponible:
        try:
            resp = requests.post(url_test, json=payload, timeout=2)
            if resp.status_code == 200:
                n8n_disponible = True
        except: pass
    
    if n8n_disponible:
        return {
            "status": "ok", 
            "modo": "n8n", 
            "scan_id": scan_id,
            "user_id": user_id,
            "mensaje": "Workflow n8n iniciado"
        }
    
    # Fallback: modo directo (sin n8n) - mismo flujo pero directo
    print(f"[BFF] Modo directo para usuario: {user_id}")
    
    # Verificar si este scanId ya fue procesado (idempotencia)
    if db_service.scan_exists(user_id, scan_id):
        return {"status": "already_processed", "scan_id": scan_id}
    
    result = scan_service.discover(target_ip)
    
    if result.get("error") == "NMAP_MISSING":
        return {"status": "error", "code": "NMAP_MISSING"}
    
    dispositivos = result.get("dispositivos", [])
    print(f"[BFF] Dispositivos encontrados: {len(dispositivos)}")
    
    escaneados = 0
    total_vulnerabilidades = 0
    
    for dispositivo in dispositivos:
        ip = dispositivo.get("ip", "")
        if ip:
            try:
                # Marcar scan como procesado antes de guardar
                db_service.mark_scan_processed(user_id, scan_id, ip)
                detalle = scan_service.deep_scan(ip, user_id, scan_id)
                escaneados += 1
                total_vulnerabilidades += detalle.get("total_vulnerabilidades", 0)
                print(f"[BFF] GUARDADO: {ip} para user: {user_id}")
            except Exception as e:
                print(f"[BFF] Error escaneando {ip}: {e}")
    
    # Finalizar el escaneo actualizando sus metadatos globales
    import datetime
    db_service.update_scan_metadata(user_id, scan_id, {
        "devices_found": escaneados,
        "vulnerabilidades_found": total_vulnerabilidades,
        "end_time": datetime.datetime.utcnow().isoformat(),
        "status": "completed"
    })
    
    print(f"[BFF] Escaneo COMPLETADO. Total: {escaneados}")
    
    return {
        "status": "ok", 
        "modo": "directo",
        "scan_id": scan_id,
        "user_id": user_id,
        "dispositivos_escaneados": escaneados,
        "mensaje": f"Escaneo completado: {escaneados} dispositivos"
    }


@router.get("/history")
def get_scan_history(user: dict = Depends(get_current_user)):
    user_id = user.get("uid", "")
    scans = db_service.get_user_scans(user_id)
    return {"status": "ok", "scans": scans}


@router.get("/history/{scan_id}")
def get_scan_details(scan_id: str, user: dict = Depends(get_current_user)):
    user_id = user.get("uid", "")
    details = db_service.get_scan_details(user_id, scan_id)
    if not details:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {"status": "ok", "details": details}


@router.get("/history/{scan_id}/devices")
def get_scan_devices(scan_id: str, user: dict = Depends(get_current_user)):
    user_id = user.get("uid", "")
    devices = db_service.get_scan_devices(user_id, scan_id)
    return {"status": "ok", "devices": devices}


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