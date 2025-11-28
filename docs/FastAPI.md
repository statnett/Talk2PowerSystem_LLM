# Talk2PowerSystem Application

## Environment variables

### Agent Configuration

* `AGENT_CONFIG` - REQUIRED - Path to the agent configuration file in yaml format.
  Check [the agent configurations here](./AgentConfig.md).

### Redis

* `REDIS_HOST` - REQUIRED - Redis connection host. For example, `localhost`.
The connection to Redis is with `redis://` protocol, i.e. TCP socket connection.
* `REDIS_PORT` - OPTIONAL, DEFAULT=`6379` - Redis connection port.
* `REDIS_CONNECT_TIMEOUT` - OPTIONAL, DEFAULT=`2` - Redis connect timeout in seconds, must be >= 1.
* `REDIS_READ_TIMEOUT` - OPTIONAL, DEFAULT=`10` - Redis read timeout in seconds, must be >= 1.
* `REDIS_HEALTHCHECK_INTERVAL` - OPTIONAL, DEFAULT=`3` - Redis health check interval in seconds, must be >= 1.
See https://redis.io/docs/latest/develop/clients/redis-py/produsage/#health-checks.
* `REDIS_USERNAME` - OPTIONAL, DEFAULT=`default` - username for basic authentication to Redis.
* `REDIS_PASSWORD` - OPTIONAL, none by default - password for basic authentication to Redis.

#### TTL

* `REDIS_TTL` - OPTIONAL, DEFAULT=`60` minutes, integer, must be >= 1 - time to live in minutes.
* `REDIS_TTL_REFRESH_ON_READ`- OPTIONAL, DEFAULT=`True`, boolean - whether to refresh TTL on read.

The semantics here is as follows: the entire memory for a conversation (all messages) are persisted for `REDIS_TTL` minutes.
If new messages are added to the conversation or the explain functionality is used, then if `REDIS_TTL_REFRESH_ON_READ=True`, the time to live is refreshed.

### HealthChecks

* `GTG_REFRESH_INTERVAL` - OPTIONAL, DEFAULT=`30` seconds, must be >= 1 - The `__gtg` endpoint refresh interval.
* `ABOUT_REFRESH_INTERVAL` - OPTIONAL, DEFAULT=`30` seconds, must be >= 1 - The `__about` endpoint refresh interval.
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

### Security

* `SECURITY_ENABLED` - OPTIONAL, DEFAULT=False, Exposed to the UI - Indicates if security is enabled.
* `SECURITY_CLIENT_ID` - REQUIRED iff `SECURITY_ENABLED=True`, Exposed to the UI - The registered application (client) ID.
* `SECURITY_FRONTEND_APP_CLIENT_ID` - REQUIRED iff `SECURITY_ENABLED=True`, Exposed to the UI - The registered frontend application (client) ID.
* `SECURITY_AUTHORITY` - REQUIRED iff `SECURITY_ENABLED=True`, Exposed to the UI - The authority URL used for authentication.
* `SECURITY_LOGOUT` - REQUIRED iff `SECURITY_ENABLED=True`, Exposed to the UI - The logout endpoint URL.
* `SECURITY_LOGIN_REDIRECT` - REQUIRED iff `SECURITY_ENABLED=True`, Exposed to the UI - The URL to redirect to after a successful login.
* `SECURITY_LOGOUT_REDIRECT` - REQUIRED iff `SECURITY_ENABLED=True`, Exposed to the UI - The URL to redirect to after logout.
* `SECURITY_OIDC_DISCOVERY_URL` - OPTIONAL, DEFAULT=`{SECURITY_AUTHORITY}/v2.0/.well-known/openid-configuration` - OpenID Connect Discovery URL.
* `SECURITY_AUDIENCE` - REQUIRED iff `SECURITY_ENABLED=True` - The expected audience of the security tokens.
* `SECURITY_ISSUER` - REQUIRED iff `SECURITY_ENABLED=True` - The expected issuer of the security tokens.
* `SECURITY_TTL` - OPTIONAL, DEFAULT=`86400` seconds (24 hours), must be >= 1 - Indicates how many seconds to cache the public keys and the issuer obtained from the OpenID Configuration endpoint.
According to [the Azure documentation](https://learn.microsoft.com/en-us/entra/identity-platform/access-tokens) a reasonable frequency to check for updates to the public keys used by Microsoft Entra ID is every 24 hours.

## Development

### Run the app locally

To run the app locally you need to point it to a running GraphDB, Redis and Azure OpenAI deployment.
You can use GraphDB from cim.ontotext.com and the Azure OpenAI deployments from Graphwise Azure account (shared in Keeper).
You need however to run Redis locally. In order to do this you can use the Redis setup from [the dev docker compose setup](../src/talk2powersystemllm/app/dev-docker-compose.yaml).
```commandline
docker compose -f src/talk2powersystemllm/app/dev-docker-compose.yaml up -d redis
```

There is a ready made chat bot config file you can use ["dev+retrieval.yaml"](../config/dev+retrieval.yaml),
but you will need to create a `.env` file with sample content

```
MANIFEST_PATH=/home/neli/workspace/Talk2PowerSystem_LLM/git-manifest.yaml
LOGGING_YAML_FILE=/home/neli/workspace/Talk2PowerSystem_LLM/src/talk2powersystemllm/app/logging.yaml
AGENT_CONFIG=/home/neli/workspace/Talk2PowerSystem_LLM/config/dev+retrieval.yaml
PYPROJECT_TOML_PATH=/home/neli/workspace/Talk2PowerSystem_LLM/pyproject.toml
TROUBLE_MD_PATH=/home/neli/workspace/Talk2PowerSystem_LLM/src/talk2powersystemllm/app/trouble.md
REDIS_HOST=localhost
REDIS_PASSWORD=DUMMY_REDIS_PASSWORD
LLM_API_KEY=***
```

```commandline
conda activate Talk2PowerSystemLLM
uvicorn talk2powersystemllm.app.server.main:app --reload --env-file .env
```

The API is started on http://127.0.0.1:8000. You can also open the API documentation at http://127.0.0.1:8000/docs.

When you're finished

```commandline
docker compose -f src/talk2powersystemllm/app/dev-docker-compose.yaml down -v --remove-orphans
```

## Docker image

The docker image starts the app on port 8000 using uvicorn server with 4 [workers](https://fastapi.tiangolo.com/deployment/server-workers/) by default.
To change the number of workers use the environment variable `WEB_CONCURRENCY`.

### File structure

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

### Environment variables

- `WEB_CONCURRENCY` - OPTIONAL, DEFAULT = `4` - number of uvicorn worker processes.

### Build and run locally

To run the image locally you need to point the app to a running GraphDB, Redis and Azure OpenAI deployment.
You can use GraphDB from cim.ontotext.com and the Azure OpenAI deployments from Graphwise Azure account (shared in Keeper).
However, you need however to run Redis locally.
There is a ready made [dev docker compose setup](../src/talk2powersystemllm/app/dev-docker-compose.yaml),
which uses the chat bot config file ["dev+retrieval.yaml"](../config/dev+retrieval.yaml).
Create a file `webapp.env` with content
```
AGENT_CONFIG=/code/config/dev+retrieval.yaml
LLM_API_KEY=<API_KEY_FROM_KEEPER>
REDIS_HOST=redis
REDIS_PASSWORD=DUMMY_REDIS_PASSWORD
```
You must replace <API_KEY_FROM_KEEPER> with the corresponding secret from Keeper.

Then execute:
```commandline
bash ./docker/generate-manifest.sh
docker buildx build --file docker/Dockerfile --tag talk2powersystem .
docker compose -f src/talk2powersystemllm/app/dev-docker-compose.yaml up -d
```

The API is started on http://127.0.0.1:8000. You can also open the API documentation at http://127.0.0.1:8000/docs.

When you're finished

```commandline
docker compose -f src/talk2powersystemllm/app/dev-docker-compose.yaml down -v --remove-orphans
```
