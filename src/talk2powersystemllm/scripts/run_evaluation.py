import argparse
from datetime import datetime, timezone
from pathlib import Path

import jsonlines
import yaml
from langgraph.graph.graph import CompiledGraph
from tqdm import tqdm
from ttyg.agents import run_agent_for_evaluation
from ttyg_evaluation import run_evaluation, compute_aggregations

from talk2powersystemllm.talk_to_power_system_agent import get_talk_to_power_system_agent
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
        "--results_dir",
        dest="results_dir",
        required=True,
        help="Path to the results directory",
    )

    return parser


def run_evaluation_on_split(
        agent: CompiledGraph,
        split: list[dict],
        split_name: str,
        results_dir: Path,
) -> None:
    chat_responses = dict()
    chat_responses_file = results_dir / f"chat_responses_{split_name}.jsonl"
    with jsonlines.open(chat_responses_file, mode="w") as writer:
        for template in tqdm(split, desc=f"Processing templates from {split_name} split"):
            for question in template["questions"]:
                chat_response = run_agent_for_evaluation(
                    agent,
                    question["id"],
                    {"messages": [("user", question["nl_question"])]}
                )
                chat_responses[question["id"]] = chat_response
                writer.write(chat_response)

    per_question_eval = run_evaluation(split, chat_responses)
    evaluation_results_file = results_dir / f"evaluation_per_question_{split_name}.yaml"
    save_as_yaml(evaluation_results_file, per_question_eval)
    aggregates = compute_aggregations(per_question_eval)
    aggregation_results = results_dir / f"evaluation_summary_{split_name}.yaml"
    save_as_yaml(aggregation_results, aggregates)


def main():
    args_parser = get_args_parser()
    args = args_parser.parse_args()

    results_dir = Path(args.results_dir)
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results_dir = results_dir / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)

    _, dev_split, test_split = load_and_split_qa_dataset(Path(args.qa_dataset_path))
    agent: CompiledGraph = get_talk_to_power_system_agent(args.chat_config_path)

    run_evaluation_on_split(agent, dev_split, "dev", results_dir)
    run_evaluation_on_split(agent, test_split, "test", results_dir)
