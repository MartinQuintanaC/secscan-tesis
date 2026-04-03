from fastapi import FastAPI
from pydantic import BaseModel
from core.scanner import ScannerEngine

app = FastAPI(
    title="SecScan API (V2 - Arquitectura Cloud)",
    description="Motor de escaneo microservicio listo para n8n y Firebase",
    version="2.0.0"
)

scanner = ScannerEngine()

class ScanRequest(BaseModel):
    target_ip: str

from core.firebase_client import FirebaseDB
import datetime

@app.get("/")
def raiz():
    return {"mensaje": "El motor SecScan V2 (Microservice) está en línea."}

@app.post("/api/test-db")
def test_cloud_database():
    """
    Ruta rápida para probar si la conexión y escritura hacia la nube de Google funciona.
    """
    # 1. Instanciamos nuestra nueva conexión a Nube
    firebase = FirebaseDB()
    db = firebase.get_db()
    
    # 2. Fabricamos un JSON (Documento NoSQL) falso
    datos_prueba = {
        "origen": "FastAPI SecScan",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "mensaje": "¡Hola Mundo! El backend ha aterrizado en la Nube."
    }
    
    # 3. Lo inyectamos forzosamente en una "Colección" de la nube llamada "tests" (Firestore la creará sola)
    db.collection("tests").add(datos_prueba)
    
    return {"status": "ok", "detalle": "Datos escritos en Firebase exitosamente. ¡Ve a revisar tu consola web!"}
