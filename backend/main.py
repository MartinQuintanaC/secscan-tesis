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

@app.get("/")
def raiz():
    return {"mensaje": "El motor SecScan V2 (Microservice) está en línea."}
