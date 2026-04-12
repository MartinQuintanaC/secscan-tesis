from pydantic import BaseModel
from typing import List, Optional

class ScanRequest(BaseModel):
    target_ip: str

class CVELookupRequest(BaseModel):
    servicio: str
    version: str
