from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.api import api_router

app = FastAPI(
    title="SecScan API (Modular V3)",
    description="Backend reestructurado con Clean Architecture",
    version="3.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def raiz():
    return {"mensaje": "SecScan Modular API está ONLINE."}

# Incluimos todas las rutas bajo el prefijo /api
app.include_router(api_router, prefix="/api")
