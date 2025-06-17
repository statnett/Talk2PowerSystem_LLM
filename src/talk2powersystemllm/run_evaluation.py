import argparse
import random
from datetime import datetime, timezone
from pathlib import Path

import yaml
from langgraph.graph.graph import CompiledGraph
from tqdm import tqdm
from ttyg.agents import run_agent_for_evaluation
from ttyg_evaluation import run_evaluation, compute_aggregations

from .talk_to_power_system_agent import get_talk_to_power_system_agent


def load_gsc(path: Path) -> tuple[list[dict], list[dict]]:
    with open(path, "r", encoding="utf-8") as file:
        gsc: list[dict] = yaml.safe_load(file)
        # filter templates with no questions; we shouldn't have such, but for now they are present
        gsc = [t for t in gsc if len(t["questions"]) > 0]

        # random split train / test (90% / 10%)
        random.seed(1)
        random.shuffle(gsc)
        split_index = int(len(gsc) * 0.90)
        return gsc[:split_index], gsc[split_index:]


def save_as_yaml(path: Path, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(obj, f, sort_keys=False)


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

    _, test_split = load_gsc(Path(args.gsc_path))
    agent: CompiledGraph = get_talk_to_power_system_agent(args.chat_config_path)

    chat_responses = dict()
    for template in tqdm(test_split, desc="Processing templates"):
        for question in template["questions"]:
            chat_responses[question["id"]] = run_agent_for_evaluation(
                agent,
                question["id"],
                {"messages": [("user", question["nl_question"])]}
            )

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    per_question_eval = run_evaluation(test_split, chat_responses)

    evaluation_results_file = results_dir / f"evaluation_per_question_{timestamp}.yaml"
    save_as_yaml(evaluation_results_file, per_question_eval)
    aggregates = compute_aggregations(per_question_eval)
    aggregation_results = results_dir / f"evaluation_summary_{timestamp}.yaml"
    save_as_yaml(aggregation_results, aggregates)
