from pydantic import BaseModel


class HealthCheck(BaseModel):
    status: str = "ok"
    environment: str = ""
    version: str = ""


class ErrorResponse(BaseModel):
    detail: str
