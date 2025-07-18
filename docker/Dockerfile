FROM python:3.12

WORKDIR /code

COPY git-manifest.yaml /code/git-manifest.yaml
COPY docker/logging.yaml /code/logging.yaml
COPY src/talk2powersystemllm/app/trouble.md /code/trouble.md
COPY src/talk2powersystemllm/ /code/talk2powersystemllm/
COPY config/ontology/ /code/config/ontology/
COPY config/*yaml /code/config/

COPY ./pyproject.toml ./poetry.lock ./README.adoc /code/

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN pip install poetry==2.1.3 && poetry install

RUN mkdir -p /code/logs && chmod 0777 /code/logs

CMD ["uvicorn", "talk2powersystemllm.app.server.main:app", "--workers", "1", "--host", "0.0.0.0", "--port", "8000"]
