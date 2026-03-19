import re
from functools import lru_cache
from importlib.metadata import version as get_pkg_version

import markdown
import toml
from fastapi import FastAPI

from talk2powersystemllm.app.server.config import AppSettings
from talk2powersystemllm.app.server.exceptions import setup_exception_handlers
from talk2powersystemllm.app.server.lifespan import lifespan
from talk2powersystemllm.app.server.logging_conf import config_logger
from talk2powersystemllm.app.server.middleware import setup_middleware
from talk2powersystemllm.app.server.routers import all_routers

API_DESCRIPTION = ("Talk2PowerSystem Chat Bot Application provides functionality for chatting with the "
                   "Talk2PowerSystem Chat bot")


@lru_cache
def get_settings():
    return AppSettings()


settings = get_settings()

config_logger(settings.logging_yaml_file)


def get_version_and_dependencies() -> tuple[str, dict[str, str]]:
    with open(str(settings.pyproject_toml_path)) as pyproject_toml_file:
        pyproject = toml.loads(pyproject_toml_file.read())
        v: str = pyproject["project"]["version"]
        dependencies: list[str] = pyproject["project"]["dependencies"]
        return v, get_dependency_to_version(dependencies)


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


def get_trouble_html():
    with open(settings.trouble_md_path, "r", encoding="utf-8") as trouble_md_file:
        trouble_md_text = trouble_md_file.read()
        return markdown.markdown(
            trouble_md_text,
            extensions=["toc", "fenced_code"],
            extension_configs={"toc": {"title": "Table of Contents"}}
        )


trouble_html = get_trouble_html()

version, API_DEPENDENCIES = get_version_and_dependencies()

app = FastAPI(
    title="Talk2PowerSystem Chat Bot Application",
    description=API_DESCRIPTION,
    version=version,
    docs_url=settings.docs_url,
    redoc_url=None,
    root_path=settings.root_path,
    lifespan=lifespan,
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }
)

app.state.settings = settings
app.state.dependencies = API_DEPENDENCIES
app.state.trouble_html = trouble_html

for router in all_routers:
    app.include_router(router)

setup_exception_handlers(app)
setup_middleware(app)
