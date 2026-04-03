from fastapi import FastAPI
from pydantic import BaseModel
from core.scanner import ScannerEngine
from core.firebase_client import FirebaseDB
import datetime

app = FastAPI(
    title="SecScan API (V2 - Arquitectura Cloud)",
    description="Motor de escaneo microservicio listo para n8n y Firebase",
    version="2.0.0"
)

scanner = ScannerEngine()
firebase = FirebaseDB()
db = firebase.get_db()

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
    Lo escanea a fondo para extraer puertos, servicios y lo persiste en Google Firebase.
    """
    puertos_info = scanner.scan_ports(ip)
    
    # Empaquetamos el objeto exacto como Documento NoSQL
    documento = {
        "ip": ip,
        "mac": puertos_info.get("mac", "Desconocida"),
        "puertos_abiertos": puertos_info.get("puertos_abiertos", []),
        "fecha_auditoria": datetime.datetime.utcnow().isoformat(),
        "estado": "Completado"
    }
    
    # Usamos la IP como el ID único del documento en la colección 'devices'
    # set() sobreescribe la IP si ya existía para mantener la base limpia.
    db.collection("devices").document(ip).set(documento)
    
    return {
        "status": "ok",
        "ip_escaneada": ip,
        "puertos_encontrados": len(puertos_info.get("puertos_abiertos", []))
    }

@app.post("/api/test-db")
def test_cloud_database():
    db.collection("tests").add({
        "origen": "FastAPI SecScan",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "mensaje": "Hola Mundo. Backend está activo."
    })
    return {"status": "ok"}
