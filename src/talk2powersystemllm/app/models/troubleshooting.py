from enum import Enum

from pydantic import BaseModel


class GoodToGoStatus(Enum):
    OK = "OK"
    UNAVAILABLE = "UNAVAILABLE"


class GoodToGoInfo(BaseModel):
    gtg: GoodToGoStatus


class HealthStatus(Enum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Severity(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class HealthCheck(BaseModel):
    status: HealthStatus
    severity: Severity
    id: str
    name: str
    type: str
    impact: str
    troubleshooting: str
    description: str
    message: str


class HealthInfo(BaseModel):
    status: HealthStatus
    healthChecks: list[HealthCheck]
