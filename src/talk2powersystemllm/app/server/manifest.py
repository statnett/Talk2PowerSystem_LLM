import toml
import yaml

from .config import settings


def read_manifest() -> dict:
    with open(settings.manifest_path, "r") as f:
        return yaml.safe_load(f.read())


git_manifest = read_manifest()
__sha__ = git_manifest["Git-SHA"]
__branch__ = git_manifest["Build-Branch"]
__timestamp__ = git_manifest["Build-Timestamp"]


def get_version() -> str:
    with open(str(settings.pyproject_toml_path)) as pyproject_toml_file:
        pyproject = toml.loads(pyproject_toml_file.read())
        version: str = pyproject["project"]["version"]
        return version


__version__ = get_version()
