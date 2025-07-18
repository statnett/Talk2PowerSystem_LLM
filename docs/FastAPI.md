# Talk2PowerSystem Application

## Environment variables

### Agent Configuration

* `AGENT_CONFIG` - REQUIRED - Path to the agent configuration file in yaml format.
  Check [the agent configurations here](./AgentConfig.md).

### HealthChecks

* `GTG_REFRESH_INTERVAL` - OPTIONAL, DEFAULT=`30` seconds, must be >= 1 - The gtg endpoint refresh interval.
* `TROUBLE_MD_PATH` - OPTIONAL, default = `/code/trouble.md` - Path to the `trouble.md` file

### Documentation

- `DOCS_URL` - OPTIONAL, default = `/docs` - The endpoint, which serves the automatic documentation / Swagger UI. Must
  start with "/". Can be "/".
- `ROOT_PATH` - OPTIONAL, default = `/` - A path prefix handled by a proxy that is not seen by the application but is
  seen by external clients,
  which affects things like Swagger UI. Read more about it at
  the [FastAPI docs for Behind a Proxy](https://fastapi.tiangolo.com/advanced/behind-a-proxy/).

### Logging

- `LOGGING_YAML_FILE` - OPTIONAL, default = `/code/logging.yaml` - Path to the logging configuration.
  Check [the official documentation](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema) on
  how to configure the logging.

### Manifest

- `MANIFEST_PATH` - OPTIONAL, default = `/code/git-manifest.yaml` - Path to the manifest file. The file must be in yaml
  format. Sample content

```yaml
Git-SHA: 'a730751ac055a4f2dad3dc3e5658bb1bf30ff412'
Build-Branch: 'COOL-BRANCH-NAME'
Build-Timestamp: '2024-01-09T13:31:49Z'
```

This information is included in the response from the `/__about` endpoint.

- `PYPROJECT_TOML_PATH` - OPTIONAL, default = `/code/pyproject.toml` - Path to the `pyproject.toml` file

The `version` information is included in the response from the `/__about` endpoint.

## Development

### Run the app locally

Create a `.env` file with sample content

```
MANIFEST_PATH=/home/neli/workspace/Talk2PowerSystem_LLM/src/talk2powersystemllm/app/dummy-manifest.yaml
LOGGING_YAML_FILE=/home/neli/workspace/Talk2PowerSystem_LLM/src/talk2powersystemllm/app/logging.yaml
AGENT_CONFIG=/home/neli/workspace/Talk2PowerSystem_LLM/config/cim.ontotext.no.cognite.yaml
PYPROJECT_TOML_PATH=/home/neli/workspace/Talk2PowerSystem_LLM/pyproject.toml
TROUBLE_MD_PATH=/home/neli/workspace/Talk2PowerSystem_LLM/src/talk2powersystemllm/app/trouble.md
GRAPHDB_PASSWORD=***
LLM_API_KEY=***
```

```commandline
conda activate Talk2PowerSystemLLM
uvicorn talk2powersystemllm.app.server.main:app --reload --env-file .env
```

The API is started on http://127.0.0.1:8000. You can also open the API documentation at http://127.0.0.1:8000/docs.

## Docker image

The docker image starts the app on port 8000 using uvicorn server.
The number of uvicorn workers is 1 and must not be increased, because for now the chatbot memory is kept into the
process memory
and increasing the number of uvicorn workers will create new processes, which will lead to users experience unexpected
behaviour.

File structure:

- `/code`
    - `README.adoc` - required by `poetry` in order to install the dependencies. Copied from
      the [README.adoc](../README.adoc)
    - `config/` - All `yaml` files from the [config directory](../config) and the `ontology` sub-directory.
    - `git-manifest.yaml` - automatically generated file during a release. The information is served from the `__about`
      endpoint of the app.
    - `logging.yaml` - Default logging configuration from [here](../docker/logging.yaml).
    - `logs/` - Directory for storing the log files.
    - `trouble.md` - Troubleshooting document of the application.
    - `poetry.lock` - required by `poetry` in order to install the dependencies.
    - `pyproject.toml` - required by `poetry` in order to install the dependencies.
    - `talk2powersystemllm` - python source code.

### Build and run locally

```commandline
cp src/talk2powersystemllm/app/dummy-manifest.yaml git-manifest.yaml
docker buildx build --file docker/Dockerfile --tag talk2powersystem .
docker run -p 8000:8000 -e AGENT_CONFIG=/code/config/cim.ontotext.no.cognite.yaml -e LLM_API_KEY=<API_KEY_FROM_KEEPER> -e GRAPHDB_PASSWORD=<GRAPHDB_PASSWORD_FROM_KEEPER> talk2powersystem
```

You must escape any `$` signs in the password with `\`!
The API is started on http://127.0.0.1:8000. You can also open the API documentation at http://127.0.0.1:8000/docs.
