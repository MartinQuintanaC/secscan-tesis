from fastapi import APIRouter, Depends
from services.db_service import DatabaseService
from api.deps import get_current_user

router = APIRouter()
db_service = DatabaseService()

@router.get("/devices")
def get_devices(user: dict = Depends(get_current_user)):
    return {"status": "ok", "dispositivos": db_service.get_all_devices()}

@router.get("/vulnerabilities")
def get_vulnerabilities(user: dict = Depends(get_current_user)):
    return {"status": "ok", "vulnerabilidades": db_service.get_all_vulnerabilities()}

@router.post("/test-db")
def test_cloud_database(user: dict = Depends(get_current_user)):
    db_service.run_db_test()
    return {"status": "ok"}
