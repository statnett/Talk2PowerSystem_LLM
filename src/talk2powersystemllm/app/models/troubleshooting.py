from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from ttyg.graphdb import GraphDBAutocompleteStatus, GraphDBRdfRankStatus

from talk2powersystemllm.agent import LLMType


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


class AboutOntologyInfo(BaseModel):
    uri: str
    name: str | None
    date: str | None
    version: str | None


class AboutDatasetInfo(BaseModel):
    uri: str
    name: str | None
    date: str | None


class AboutGraphDBInfo(BaseModel):
    base_url: str = Field(alias="baseUrl")
    repository: str
    version: str
    number_of_explicit_triples: int = Field(alias="numberOfExplicitTriples")
    number_of_triples: int = Field(alias="numberOfTriples")
    autocomplete_index_status: GraphDBAutocompleteStatus = Field(alias="autocompleteIndexStatus")
    rdf_rank_status: GraphDBRdfRankStatus = Field(alias="rdfRankStatus")


class AboutLLMInfo(BaseModel):
    type: LLMType
    model: str
    temperature: float
    seed: int


class AboutAgentInfo(BaseModel):
    assistant_instructions: str = Field(alias="assistantInstructions")
    llm: AboutLLMInfo
    tools: dict[str, dict[str, Any]]


class AboutBackendInfo(BaseModel):
    description: str
    version: str
    build_date: str = Field(alias="buildDate")
    build_branch: str = Field(alias="buildBranch")
    git_sha: str = Field(alias="gitSHA")
    python_version: str = Field(alias="pythonVersion")
    dependencies: dict[str, str]


class AboutInfo(BaseModel):
    ontologies: list[AboutOntologyInfo]
    datasets: list[AboutDatasetInfo]
    graphdb: AboutGraphDBInfo
    agent: AboutAgentInfo
    backend: AboutBackendInfo
