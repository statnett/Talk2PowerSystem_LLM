import re
from functools import lru_cache
from importlib.metadata import version as get_pkg_version
from pathlib import Path

import toml
from fastapi import FastAPI

from talk2powersystemllm.app.server.config import AppSettings
from talk2powersystemllm.app.server.exceptions import setup_exception_handlers
from talk2powersystemllm.app.server.lifespan import lifespan
from talk2powersystemllm.app.server.logging_conf import config_logger
from talk2powersystemllm.app.server.middleware import setup_middleware
from talk2powersystemllm.app.server.routers import all_routers


@lru_cache
def get_settings():
    return AppSettings()


def get_version_and_dependencies(
    pyproject_toml_path: Path,
) -> tuple[str, dict[str, str]]:
    with open(str(pyproject_toml_path)) as pyproject_toml_file:
        pyproject = toml.loads(pyproject_toml_file.read())
        version: str = pyproject["project"]["version"]
        dependencies: list[str] = pyproject["project"]["dependencies"]
        return version, get_dependency_to_version(dependencies)


def get_dependency_to_version(dependencies: list[str]) -> dict[str, str]:
    dependency_to_version: dict[str, str] = {}
    dependency_regex = re.compile(
        r"^([a-zA-Z0-9._-]+)(\[[a-zA-Z0-9._,-]+])?(?:\s*[<>=!~^]+\s*[\w.\-]+(?:,?\s*[<>=!~^]+\s*[\w.\-]+)*)?$"
    )
    for dependency in dependencies:
        match = re.match(dependency_regex, dependency)
        if match:
            base_name = match.group(1)
            extras = match.group(2) if match.group(2) else ""
            display_name = f"{base_name}{extras}"
            dependency_to_version[display_name] = get_pkg_version(base_name)
    return dependency_to_version


def create_app() -> FastAPI:
    settings = get_settings()

    config_logger(settings.logging_yaml_file)

    version, dependencies = get_version_and_dependencies(settings.pyproject_toml_path)

    fastapi_app = FastAPI(
        title="Talk2PowerSystem Chat Bot Application",
        description="Talk2PowerSystem Chat Bot Application provides functionality "
        "for chatting with the Talk2PowerSystem Chat bot",
        version=version,
        docs_url=settings.docs_url,
        redoc_url=None,
        root_path=settings.root_path,
        lifespan=lifespan,
        license_info={
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
    )

    fastapi_app.state.settings = settings
    fastapi_app.state.dependencies = dependencies

    for router in all_routers:
        fastapi_app.include_router(router)

    setup_exception_handlers(fastapi_app)
    setup_middleware(fastapi_app)
    return fastapi_app


app = create_app()
