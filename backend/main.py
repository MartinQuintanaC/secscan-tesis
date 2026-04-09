from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.scanner import ScannerEngine
from core.firebase_client import FirebaseDB
from core.cve_client import CVEClient
import datetime
import requests

app = FastAPI(
    title="SecScan API (V2 - Arquitectura Cloud)",
    description="Motor de escaneo microservicio listo para n8n y Firebase",
    version="2.0.0"
)

# CORS: Permite que el frontend de React (puerto 5173) hable con este backend (puerto 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scanner = ScannerEngine()
firebase = FirebaseDB()
db = firebase.get_db()
cve_client = CVEClient()

class ScanRequest(BaseModel):
    target_ip: str

@app.get("/")
def raiz():
    return {"mensaje": "El motor SecScan V2 (Microservice) está en línea."}

@app.post("/api/discover")
def discover_network(request: ScanRequest):
    """
    Ruta Atómica 1: Usada por n8n para obtener TODAS las IPs vivas de un cajón.
    """
    # Limpiamos errores de tipeo de n8n (ej: '=192.168...')
    ip_limpia = request.target_ip.replace('=', '').strip() if request.target_ip else ''
    
    # Si detectamos instrucción automática (Zero Configure), calculamos la subred en pleno vuelo
    from core.scanner import get_local_cidr
    if ip_limpia.lower() == "auto" or ip_limpia == "":
        ip_real = get_local_cidr()
    else:
        ip_real = ip_limpia
        
    dispositivos_vivos = scanner.discover_network(ip_real)
    print("====== REPORTE DE NMAP (DISCOVER) ======")
    print(f"IP Solicitada: {request.target_ip}")
    print(f"Encontrados: {len(dispositivos_vivos)}")
    print(dispositivos_vivos)
    print("========================================")
    return {
        "status": "ok", 
        "total": len(dispositivos_vivos),
        "dispositivos": dispositivos_vivos
    }

@app.post("/api/deep-scan/{ip}")
def deep_scan_device(ip: str):
    """
    Ruta Atómica 2: Recibe solo UNA IP (típicamente enviada por n8n o el Dashboard).
    Escanea puertos, detecta versiones, cruza con CVEs del NVD y persiste TODO en Firebase.
    """
    print(f"====== N8N PIDIÓ ESCANEO PROFUNDO PARA: {ip} ======")
    puertos_info = scanner.scan_ports(ip)
    puertos = puertos_info.get("puertos_abiertos", [])
    
    total_vulnerabilidades = 0
    for puerto in puertos:
        servicio = puerto.get("servicio", "")
        version = puerto.get("version", "")
        
        if version and version.strip() != "":
            cves = cve_client.buscar_vulnerabilidades(servicio, version)
            puerto["vulnerabilidades"] = cves
            total_vulnerabilidades += len(cves)
        else:
            puerto["vulnerabilidades"] = []
    
    mac_real = puertos_info.get("mac", "Desconocida")
    # Para el historial inmutable, el pasaporte es la MAC. Si está oculta, usamos la IP.
    id_unico = mac_real if mac_real != "Desconocida" else ip
    
    doc_ref = db.collection("historial").document(id_unico)
    doc_snap = doc_ref.get()
    
    hora_actual = datetime.datetime.utcnow().isoformat()
    es_nuevo = False
    primera_conexion = hora_actual
    
    if not doc_snap.exists:
        # ¡ALERTA DE INTRUSO! Es la primera vez que esta red ve a esta máquina.
        es_nuevo = True
        doc_ref.set({
            "ip_inicial": ip,
            "mac": mac_real,
            "primera_conexion": hora_actual,
            "fabricante": puertos_info.get("fabricante", "Desconocido")
        })
    else:
        # Ya es conocido, rescatamos a qué hora entró por el transcurso de los tiempos
        datos_historial = doc_snap.to_dict()
        primera_conexion = datos_historial.get("primera_conexion", hora_actual)
        
    documento = {
        "ip": ip,
        "mac": mac_real,
        "fabricante": puertos_info.get("fabricante", "Desconocido"),
        "puertos_abiertos": puertos,
        "total_vulnerabilidades": total_vulnerabilidades,
        "fecha_auditoria": hora_actual,
        "estado": "Completado",
        "es_nuevo": es_nuevo,
        "primera_conexion": primera_conexion
    }
    
    db.collection("devices").document(ip).set(documento)
    
    if total_vulnerabilidades > 0:
        for puerto in puertos:
            for cve in puerto.get("vulnerabilidades", []):
                doc_vuln = {
                    "ip": ip,
                    "puerto": puerto.get("puerto"),
                    "servicio": puerto.get("servicio"),
                    "version": puerto.get("version"),
                    "cve_id": cve["cve_id"],
                    "descripcion": cve["descripcion"],
                    "severidad": cve["severidad"],
                    "score": cve["score"],
                    "fecha_deteccion": datetime.datetime.utcnow().isoformat()
                }
                db.collection("vulnerabilities").document(cve["cve_id"]).set(doc_vuln)
    
    return {
        "status": "ok",
        "ip_escaneada": ip,
        "puertos_encontrados": len(puertos),
        "vulnerabilidades_encontradas": total_vulnerabilidades,
        "detalle": documento
    }

@app.post("/api/trigger-scan")
def trigger_scan(request: ScanRequest):
    """
    Ruta Puente: React llama aquí y Python dispara el webhook de n8n.
    Evita los molestos bloqueos de CORS del navegador web.
    """
    # Intentamos pegarle tanto a la ruta de Producción como a la de Pruebas
    # Así garantizamos que se dispare sin importar en qué modo tengas n8n
    url_prod = "http://localhost:5678/webhook/secscan"
    url_test = "http://localhost:5678/webhook-test/secscan"
    
    try:
        requests.post(url_prod, json={"target_ip": request.target_ip}, timeout=1)
    except:
        pass
        
    try:
        requests.post(url_test, json={"target_ip": request.target_ip}, timeout=1)
    except:
        pass
        
    return {"status": "ok", "mensaje": "Webhook disparado con éxito"}

@app.get("/api/devices")
def get_devices():
    """
    Lectura: Devuelve todos los dispositivos almacenados en Firebase.
    Usado por el Dashboard para mostrar el historial.
    """
    docs = db.collection("devices").stream()
    dispositivos = []
    for doc in docs:
        dispositivos.append(doc.to_dict())
    return {"status": "ok", "dispositivos": dispositivos}

@app.get("/api/vulnerabilities")
def get_vulnerabilities():
    """
    Lectura: Devuelve todas las vulnerabilidades almacenadas en Firebase.
    Usado por el Dashboard para el historial de amenazas.
    """
    docs = db.collection("vulnerabilities").stream()
    vulns = []
    for doc in docs:
        vulns.append(doc.to_dict())
    # Ordenamos por score descendente (las más peligrosas primero)
    vulns.sort(key=lambda x: x.get("score", 0), reverse=True)
    return {"status": "ok", "vulnerabilidades": vulns}

@app.post("/api/cve-lookup")
def cve_lookup(servicio: str, version: str):
    """
    Ruta Atómica 3: Consulta directa al NVD.
    """
    resultados = cve_client.buscar_vulnerabilidades(servicio, version)
    return {
        "status": "ok",
        "servicio": servicio,
        "version": version,
        "total_cves": len(resultados),
        "vulnerabilidades": resultados
    }

@app.post("/api/test-db")
def test_cloud_database():
    db.collection("tests").add({
        "origen": "FastAPI SecScan",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "mensaje": "Hola Mundo. Backend está activo."
    })
    return {"status": "ok"}
