import argparse
import io
import json
import time
import uuid
from base64 import b64encode
from datetime import timezone, datetime
from pathlib import Path

import requests
import yaml
from graphrag_eval import run_evaluation, compute_aggregates
from pydantic import SecretStr, Field, model_validator
from pydantic_settings import BaseSettings
from requests import Response
from tenacity import retry, stop_after_attempt, wait_exponential, RetryCallState
from tqdm import tqdm
from ttyg.graphdb import GraphDB

from talk2powersystemllm.qa_dataset import load_and_split_qa_dataset


def get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Talk to Power System LLM Quality")
    parser.add_argument(
        "--path_to_graphdb_config_yaml",
        dest="path_to_graphdb_config_yaml",
        required=True,
        help="Path to GraphDB config yaml file",
    )
    parser.add_argument(
        "--qa-dataset-path",
        dest="qa_dataset_path",
        required=True,
        help="Path to the Q&A dataset serialized in the expected yaml format",
    )
    parser.add_argument(
        "--n_templates",
        dest="n_templates",
        type=int,
        required=False,
        default=50,
        help="Limit the number of templates",
    )
    parser.add_argument(
        "--results_dir",
        dest="results_dir",
        required=True,
        help="Path to the results directory",
    )

    return parser


class GraphDBWrapper(GraphDB):
    """We need to override the class, because currently GraphDB /rest/chat/conversations/explain rest endpoint
     doesn't return the actual executed SPARQL query, i.e. if missing prefixes are automatically added, they are not
     present in the response. However, the original implementation also checks for IRIs in the SPARQL queries,
     which are missing in the KG, but we want to skip this check here."""

    def _GraphDB__validate_query(self, query: str) -> str:
        parsed_query = self._GraphDB__parse_query(query)
        prefix_part = str(parsed_query[0])
        query_part = str(parsed_query[1:])

        defined_prefixes = self._GraphDB__get_defined_prefixes(prefix_part)
        known_prefixes = self.get_known_prefixes()

        query = self._GraphDB__correct_wrong_prefixes(defined_prefixes, known_prefixes, query)

        prefixed_iris = self._GraphDB__get_prefixed_iris(query_part)

        query = self._GraphDB__add_missing_prefixes(defined_prefixes, known_prefixes, prefixed_iris, query)

        return query


class GraphDBSettings(BaseSettings):
    model_config = {
        "env_prefix": "GRAPHDB_",
    }

    base_url: str
    repository_id: str
    connect_timeout: int = Field(default=2, ge=1)
    read_timeout: int = Field(default=10, ge=1)
    sparql_timeout: int = Field(default=15, ge=1)
    ttyg_agent_id: str
    username: str | None = None
    password: SecretStr | None = None

    @model_validator(mode="after")
    def check_password_required_if_username(self) -> "GraphDBSettings":
        username = self.username
        password = self.password
        if username and not password:
            raise ValueError("password is required if username is provided")
        return self


def save_as_yaml(path: Path, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(obj, f, sort_keys=False)


def run_agent(
        writer: io.TextIOWrapper,
        graphdb_settings: GraphDBSettings,
        question_id: str,
        question_text: str,
) -> None:
    writer.write(str(question_id))
    writer.write("\n")
    x_request_id_prefix = f"SN-142-{question_id}-{uuid.uuid1()}"
    writer.write(str(x_request_id_prefix))
    writer.write("\n")

    try:
        start = time.time()
        conversations_response = post_conversations(x_request_id_prefix, graphdb_settings, question_text)
    except requests.exceptions.HTTPError as e:
        writer.write(json.dumps({
            "question_id": question_id,
            "error": str(e),
            "status": "error",
        }))
        writer.write("\n\n\n\n\n")
        return

    conversations_response_body = conversations_response.json()
    elapsed_sec = time.time() - start
    writer.write(json.dumps(conversations_response_body))
    writer.write("\n")
    writer.write(str(elapsed_sec))
    writer.write("\n")

    messages = conversations_response_body["messages"]
    conversation_id = conversations_response_body["id"]

    explain_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Request-Id": f"{x_request_id_prefix}-explain",
    }
    if graphdb_settings.username:
        explain_headers.update({
            "Authorization": "Basic " + b64encode(
                f"{graphdb_settings.username}:{graphdb_settings.password.get_secret_value()}".encode("ascii")
            ).decode()
        })
    explain_response = requests.post(
        f"{graphdb_settings.base_url}/rest/chat/conversations/explain",
        headers=explain_headers,
        json={
            "conversationId": conversation_id,
            "answerId": messages[-1]["id"],
        },
        timeout=(graphdb_settings.connect_timeout, graphdb_settings.read_timeout)
    )
    explain_response.raise_for_status()
    explain_response_body = explain_response.json()
    writer.write(json.dumps(explain_response_body))
    writer.write("\n")

    delete_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Request-Id": f"{x_request_id_prefix}-delete",
    }
    if graphdb_settings.username:
        delete_headers.update({
            "Authorization": "Basic " + b64encode(
                f"{graphdb_settings.username}:{graphdb_settings.password.get_secret_value()}".encode("ascii")
            ).decode()
        })
    delete_response = requests.delete(
        f"{graphdb_settings.base_url}/rest/chat/conversations/{conversation_id}",
        headers=delete_headers,
        timeout=(graphdb_settings.connect_timeout, graphdb_settings.read_timeout)
    )
    delete_response.raise_for_status()
    delete_response_body = delete_response.json()
    writer.write(json.dumps(delete_response_body))
    writer.write("\n")

    writer.write("\n")


def log_retry(retry_state: RetryCallState):
    print(retry_state)


@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    before_sleep=log_retry
)
def post_conversations(
        x_request_id_prefix: str,
        graphdb_settings: GraphDBSettings,
        question_text: str,
        retry_state: RetryCallState = None
) -> Response:
    attempt_number = retry_state.attempt_number if retry_state else 1

    conversations_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Request-Id": f"{x_request_id_prefix}-{attempt_number}-conversations",
    }
    if graphdb_settings.username:
        conversations_headers.update({
            "Authorization": "Basic " + b64encode(
                f"{graphdb_settings.username}:{graphdb_settings.password.get_secret_value()}".encode("ascii")
            ).decode()
        })

    conversations_response = requests.post(
        f"{graphdb_settings.base_url}/rest/chat/conversations",
        headers=conversations_headers,
        json={
            "agentId": graphdb_settings.ttyg_agent_id,
            "question": question_text,
        },
        timeout=(graphdb_settings.connect_timeout, graphdb_settings.read_timeout)
    )
    conversations_response.raise_for_status()
    return conversations_response


def init_graphdb(graphdb_settings: GraphDBSettings) -> GraphDBWrapper:
    kwargs = {
        "base_url": graphdb_settings.base_url,
        "repository_id": graphdb_settings.repository_id,
        "connect_timeout": graphdb_settings.connect_timeout,
        "read_timeout": graphdb_settings.read_timeout,
        "sparql_timeout": graphdb_settings.sparql_timeout,
    }
    if graphdb_settings.username:
        kwargs.update({
            "auth_header": "Basic " + b64encode(
                f"{graphdb_settings.username}:{graphdb_settings.password.get_secret_value()}".encode("ascii")
            ).decode()
        })
    return GraphDBWrapper(**kwargs)


def run_evaluation_on_split(
        graphdb_settings: GraphDBSettings,
        split: list[dict],
        split_name: str,
        results_dir: Path,
) -> None:
    gdb_responses_file = results_dir / f"gdb_responses_{split_name}.txt"

    with open(gdb_responses_file, mode="w") as writer:
        for template in tqdm(split, desc=f"Processing templates from {split_name} split"):
            for question in template["questions"]:
                run_agent(
                    writer,
                    graphdb_settings,
                    question["id"],
                    question["question_text"],
                )

    graphdb_client = init_graphdb(graphdb_settings)
    chat_responses_actual_answers = dict()
    chat_responses = dict()
    with open(gdb_responses_file, encoding="utf-8") as reader:
        lines = reader.readlines()
        lines = [line.strip() for line in lines]

        for i in range(0, len(lines), 7):
            responses_for_question = lines[i:i + 7]

            question_id = responses_for_question[0]
            conversations_response_body = json.loads(responses_for_question[2])
            if "status" in conversations_response_body and conversations_response_body["status"] == "error":
                chat_responses[question_id] = conversations_response_body
            else:
                elapsed_sec = responses_for_question[3]

                usage = conversations_response_body["usage"]
                messages = conversations_response_body["messages"]

                explain_response_body = json.loads(responses_for_question[4])
                query_methods = explain_response_body["queryMethods"]
                actual_steps = []
                for query_method in query_methods:
                    if query_method["errorOutput"] is not None:
                        status = "error"
                        output = query_method["errorOutput"]
                    else:
                        status = "success"
                        results, _ = graphdb_client.eval_sparql_query(query_method["query"])
                        output = results

                    if query_method["name"] == "sparql_query":
                        name, args = "sparql_query", {"query": query_method["rawQuery"]}
                    elif query_method["name"] == "autocomplete_iri_discovery_search":
                        name, args = "autocomplete_search", json.loads(query_method["rawQuery"])
                    elif query_method["name"] == "fts_search":
                        name, args = "fts_search", {"query": query_method["rawQuery"]}
                    actual_steps.append({
                        "name": name,
                        "args": args,
                        "id": str(uuid.uuid4()),
                        "status": status,
                        "output": json.dumps(output),
                    })

                chat_responses_actual_answers[question_id] = messages[-1]["message"]
                chat_responses[question_id] = {
                    "question_id": question_id,
                    "input_tokens": usage["promptTokens"],
                    "output_tokens": usage["completionTokens"],
                    "total_tokens": usage["totalTokens"],
                    "elapsed_sec": float(elapsed_sec),
                    "actual_steps": actual_steps,
                }

    per_question_eval = run_evaluation(split, chat_responses)
    for question_eval in per_question_eval:
        question_eval["actual_answer"] = chat_responses_actual_answers.get(question_eval["question_id"], None)
    evaluation_results_file = results_dir / f"evaluation_per_question_{split_name}.yaml"
    save_as_yaml(evaluation_results_file, per_question_eval)
    aggregates = compute_aggregates(per_question_eval)
    aggregation_results = results_dir / f"evaluation_summary_{split_name}.yaml"
    save_as_yaml(aggregation_results, aggregates)


def main():
    args_parser = get_args_parser()
    args = args_parser.parse_args()

    with open(args.path_to_graphdb_config_yaml, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f.read())
        graphdb_settings = GraphDBSettings(**config)

    results_dir = Path(args.results_dir)
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results_dir = results_dir / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)

    _, dev_split, test_split = load_and_split_qa_dataset(Path(args.qa_dataset_path), n_templates=args.n_templates)

    run_evaluation_on_split(graphdb_settings, dev_split, "dev", results_dir)
    run_evaluation_on_split(graphdb_settings, test_split, "test", results_dir)


if __name__ == '__main__':
    main()
