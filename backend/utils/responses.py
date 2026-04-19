from typing import Any, Optional
from fastapi.responses import JSONResponse

def success_response(data: Any, message: str = "OK", **extra_fields) -> dict:
    """Construye una respuesta exitosa estándar."""
    response = {
        "status": "ok",
        "message": message,
        **data,
        **extra_fields
    }
    return response

def error_response(code: str, message: str, details: Optional[Any] = None) -> dict:
    """Construye una respuesta de error estándar."""
    response = {
        "status": "error",
        "code": code,
        "message": message
    }
    if details:
        response["details"] = details
    return response

def paginated_response(items: list, total: int, page: int = 1, page_size: int = 50) -> dict:
    """Construye una respuesta paginada."""
    return {
        "status": "ok",
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }