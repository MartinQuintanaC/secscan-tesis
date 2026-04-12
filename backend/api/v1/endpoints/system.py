from fastapi import APIRouter
from core.installer import install_nmap_silently
from services.scan_service import ScanService

router = APIRouter()
scan_service = ScanService()

@router.get("/health")
def health_check():
    return {
        "status": "ok", 
        "nmap_installed": getattr(scan_service.scanner, 'nmap_installed', True)
    }

@router.post("/install-nmap")
def auto_install_nmap():
    success = install_nmap_silently()
    if success:
        if hasattr(scan_service.scanner, 'reload_engine'):
            scan_service.scanner.reload_engine()
        return {"status": "ok", "mensaje": "Nmap instalado en sistema host."}
    return {"status": "error", "mensaje": "Falló la instalación desatendida."}
