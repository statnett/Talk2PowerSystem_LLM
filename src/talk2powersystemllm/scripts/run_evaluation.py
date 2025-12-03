import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonlines
import yaml
from graphrag_eval import run_evaluation, compute_aggregates
from langgraph.graph.state import CompiledStateGraph
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_result
from tqdm import tqdm
from ttyg.agents import run_agent_for_evaluation

from talk2powersystemllm.agent import Talk2PowerSystemAgentFactory
from talk2powersystemllm.qa_dataset import load_and_split_qa_dataset


def save_as_yaml(path: Path, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(obj, f, sort_keys=False)


def get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Talk to Power System LLM Quality")
    parser.add_argument(
        "--chat_config_path",
        dest="chat_config_path",
        required=True,
        help="Path to the chat config.yaml file",
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


def run_evaluation_on_split(
        agent: CompiledStateGraph,
        split: list[dict],
        split_name: str,
        results_dir: Path,
) -> None:
    chat_responses_actual_answers = dict()
    chat_responses = dict()
    chat_responses_file = results_dir / f"chat_responses_{split_name}.jsonl"
    with jsonlines.open(chat_responses_file, mode="w") as writer:
        for template in tqdm(split, desc=f"Processing templates from {split_name} split"):
            for question in template["questions"]:
                chat_response = run_agent(agent, question)
                writer.write(chat_response)
                chat_responses_actual_answers[question["id"]] = chat_response.pop("actual_answer", None)
                chat_responses[question["id"]] = chat_response

    per_question_eval = run_evaluation(split, chat_responses)
    for question_eval in per_question_eval:
        question_eval["actual_answer"] = chat_responses_actual_answers[question_eval["question_id"]]
    evaluation_results_file = results_dir / f"evaluation_per_question_{split_name}.yaml"
    save_as_yaml(evaluation_results_file, per_question_eval)
    aggregates = compute_aggregates(per_question_eval)
    aggregation_results = results_dir / f"evaluation_summary_{split_name}.yaml"
    save_as_yaml(aggregation_results, aggregates)


def is_error_response(response: dict[str, Any]) -> bool:
    """Return True if the response indicates an error (i.e., we should retry)."""
    return "status" in response and response["status"] == "error"


@retry(
    retry=retry_if_result(is_error_response),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=60)
)
def run_agent(agent: CompiledStateGraph, question: dict) -> dict[str, Any]:
    chat_response = run_agent_for_evaluation(
        agent,
        question["id"],
        {"messages": [("user", question["question_text"])]}
    )
    if "status" in chat_response and chat_response["status"] == "error":
        print(
            f"Warning: The chat response for the question with id {question['id']} "
            f"is {chat_response["error"]}"
        )
    return chat_response


def main():
    args_parser = get_args_parser()
    args = args_parser.parse_args()

    results_dir = Path(args.results_dir)
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results_dir = results_dir / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)

    _, dev_split, test_split = load_and_split_qa_dataset(Path(args.qa_dataset_path), n_templates=args.n_templates)
    agent: CompiledStateGraph = Talk2PowerSystemAgentFactory(
        Path(args.chat_config_path),
    ).get_agent()

    run_evaluation_on_split(agent, dev_split, "dev", results_dir)
    run_evaluation_on_split(agent, test_split, "test", results_dir)
