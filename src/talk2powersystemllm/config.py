from pathlib import Path
from typing import Optional, Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings


class GraphDBSettings(BaseSettings):
    model_config = {
        "env_prefix": "GRAPHDB_",
    }

    base_url: str
    repository_id: str
    username: Optional[str] = None
    password: Optional[SecretStr] = None

    @model_validator(mode="after")
    @classmethod
    def check_password_required_if_username(cls, values: Any) -> Any:
        username = values.username
        password = values.password
        if username and not password:
            raise ValueError("password is required if username is provided")
        return values


class OntologySchemaSettings(BaseModel):
    file_path: Path


class AutocompleteSearchSettings(BaseModel):
    property_path: str
    sparql_query_template: Optional[str] = None


class RetrievalSearchSettings(BaseModel):
    graphdb: GraphDBSettings
    connector_name: str
    name: str
    description: str
    sparql_query_template: str
    score: float = Field(default=0, ge=0.0, le=1.0)


class CogniteSettings(BaseModel):
    cdf_project: str
    tenant_id: str
    client_name: str
    base_url: str
    interactive_client_id: str
    client_secret: Optional[SecretStr] = None


class ToolsSettings(BaseModel):
    ontology_schema: OntologySchemaSettings
    autocomplete_search: AutocompleteSearchSettings
    retrieval_search: Optional[RetrievalSearchSettings] = None
    cognite: Optional[CogniteSettings] = None


class LLMSettings(BaseSettings):
    model_config = {
        "env_prefix": "LLM_",
    }

    azure_endpoint: str
    model: str
    api_version: str
    temperature: float = Field(default=0, ge=0.0, le=2.0)
    seed: int
    timeout: int
    api_key: SecretStr


class PromptsSettings(BaseModel):
    assistant_instructions: str


class AppSettings(BaseSettings):
    graphdb: GraphDBSettings
    llm: LLMSettings
    tools: ToolsSettings
    prompts: PromptsSettings


def read_config(path_to_yaml_config: Path) -> AppSettings:
    config_path = Path(path_to_yaml_config).resolve()

    # Resolve paths relative to config file
    env_path = config_path.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f.read())

    ontology_schema_config = config["tools"]["ontology_schema"]
    rel_path = ontology_schema_config["file_path"]
    abs_path = config_path.parent / rel_path
    ontology_schema_config["file_path"] = str(abs_path.resolve())
    return AppSettings(**config)
