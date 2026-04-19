from pydantic import BaseModel
from typing import List, Optional

class ScanRequest(BaseModel):
    target_ip: str
    scan_id: Optional[str] = None
    user_id: Optional[str] = None


class CVELookupRequest(BaseModel):
    servicio: str
    version: str
