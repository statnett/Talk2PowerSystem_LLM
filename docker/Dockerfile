FROM python:3.12.11-slim AS requirements-stage

WORKDIR /tmp

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

COPY ./pyproject.toml ./poetry.lock ./README.adoc /tmp/

RUN pip install --upgrade pip && pip install poetry==2.1.3
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-root

FROM python:3.12.11-slim

ENV VIRTUAL_ENV=/tmp/.venv \
    PATH="/tmp/.venv/bin:$PATH" \
    WEB_CONCURRENCY=${WEB_CONCURRENCY:-4}

WORKDIR /code

COPY --from=requirements-stage ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY git-manifest.yaml /code/git-manifest.yaml
COPY docker/logging.yaml /code/logging.yaml
COPY src/talk2powersystemllm/app/trouble.md /code/trouble.md
COPY src/talk2powersystemllm/ /code/talk2powersystemllm/
COPY config/ontology/ /code/config/ontology/
COPY config/*yaml /code/config/
COPY ./pyproject.toml /code/

RUN mkdir -p /code/logs && chmod 0777 /code/logs

CMD exec uvicorn talk2powersystemllm.app.server.main:app --workers "$WEB_CONCURRENCY" --host 0.0.0.0 --port 8000
