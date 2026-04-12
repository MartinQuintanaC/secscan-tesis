from fastapi import APIRouter
from services.db_service import DatabaseService

router = APIRouter()
db_service = DatabaseService()

@router.get("/devices")
def get_devices():
    return {"status": "ok", "dispositivos": db_service.get_all_devices()}

@router.get("/vulnerabilities")
def get_vulnerabilities():
    return {"status": "ok", "vulnerabilidades": db_service.get_all_vulnerabilities()}

@router.post("/test-db")
def test_cloud_database():
    db_service.run_db_test()
    return {"status": "ok"}
