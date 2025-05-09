import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from tqdm import tqdm
from ttyg.agents import run_agent_for_evaluation
from ttyg_evaluation import run_evaluation, compute_aggregations

from .talk_to_power_system_agent import get_talk_to_power_system_agent


def load_gsc(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_as_json_file(path: Path, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Chat bot")
    parser.add_argument(
        "--chat_config_path",
        dest="chat_config_path",
        required=True,
        help="Path to the chat config.yaml file",
    )
    parser.add_argument(
        "--gsc-path",
        dest="gsc_path",
        required=True,
        help="Path to the gold standard",
    )
    parser.add_argument(
        "--results_dir",
        dest="results_dir",
        required=True,
        help="Path to the results directory",
    )

    return parser


def main():
    args_parser = get_args_parser()
    args = args_parser.parse_args()

    agent = get_talk_to_power_system_agent(args.chat_config_path)
    gsc = load_gsc(Path(args.gsc_path))

    chat_responses = dict()
    for template in tqdm(gsc, desc="Processing templates"):
        for question in template["qaSet"]:
            chat_responses[question["question_id"]] = run_agent_for_evaluation(
                agent,
                question["question_id"],
                {"messages": [("user", question["question"])]}
            )

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    per_question_eval = run_evaluation(load_gsc(args.gsc_path), chat_responses)

    evaluation_results_file = results_dir / f"evaluation_per_question_{timestamp}.json"
    save_as_json_file(evaluation_results_file, per_question_eval)
    aggregates = compute_aggregations(per_question_eval)
    aggregation_results = results_dir / f"evaluation_summary_{timestamp}.json"
    save_as_json_file(aggregation_results, aggregates)
