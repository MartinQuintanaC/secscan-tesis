from fastapi import FastAPI
from pydantic import BaseModel
from core.scanner import ScannerEngine
from core.firebase_client import FirebaseDB
from core.cve_client import CVEClient
import datetime

app = FastAPI(
    title="SecScan API (V2 - Arquitectura Cloud)",
    description="Motor de escaneo microservicio listo para n8n y Firebase",
    version="2.0.0"
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
    Retorna la lista cruda y rapidísima para que n8n pueda iterarlas en paralelo.
    """
    dispositivos_vivos = scanner.discover_network(request.target_ip)
    return {
        "status": "ok", 
        "total": len(dispositivos_vivos),
        "dispositivos": dispositivos_vivos
    }

@app.post("/api/deep-scan/{ip}")
def deep_scan_device(ip: str):
    """
    Ruta Atómica 2: Recibe solo UNA IP (típicamente enviada por un nodo de n8n).
    Escanea puertos, detecta versiones, cruza con CVEs del NVD y persiste TODO en Firebase.
    """
    puertos_info = scanner.scan_ports(ip)
    puertos = puertos_info.get("puertos_abiertos", [])
    
    # Para cada puerto abierto que tenga versión detectada, cruzamos con la base CVE mundial
    total_vulnerabilidades = 0
    for puerto in puertos:
        servicio = puerto.get("servicio", "")
        version = puerto.get("version", "")
        
        # Solo consultamos NVD si Nmap logró extraer una versión real
        if version and version.strip() != "":
            cves = cve_client.buscar_vulnerabilidades(servicio, version)
            puerto["vulnerabilidades"] = cves
            total_vulnerabilidades += len(cves)
        else:
            puerto["vulnerabilidades"] = []
    
    # Empaquetamos el documento completo (puertos + vulnerabilidades) como NoSQL
    documento = {
        "ip": ip,
        "mac": puertos_info.get("mac", "Desconocida"),
        "puertos_abiertos": puertos,
        "total_vulnerabilidades": total_vulnerabilidades,
        "fecha_auditoria": datetime.datetime.utcnow().isoformat(),
        "estado": "Completado"
    }
    
    # Persistimos en Firebase (colección 'devices')
    db.collection("devices").document(ip).set(documento)
    
    # Si encontramos vulnerabilidades, también las guardamos en una colección dedicada
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
        "vulnerabilidades_encontradas": total_vulnerabilidades
    }

@app.post("/api/cve-lookup")
def cve_lookup(servicio: str, version: str):
    """
    Ruta Atómica 3: Consulta directa al NVD.
    Permite buscar vulnerabilidades de un software + versión específicos sin escanear.
    Útil para consultas manuales desde Swagger o desde n8n.
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
