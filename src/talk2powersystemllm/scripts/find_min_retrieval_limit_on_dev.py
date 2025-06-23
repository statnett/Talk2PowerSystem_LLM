import argparse
from pathlib import Path

from ttyg.graphdb import GraphDB

from talk2powersystemllm.qa_dataset import load_and_split_qa_dataset, find_global_min_limit


def get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Talk to Power System LLM Quality")
    parser.add_argument(
        "--qa-dataset-path",
        dest="qa_dataset_path",
        required=True,
        help="Path to the Q&A dataset serialized in the expected yaml format",
    )
    parser.add_argument(
        "--graph_base_url",
        dest="graph_base_url",
        required=True,
        help="GraphDB base url, for example http://localhost:7200",
    )
    parser.add_argument(
        "--graph_repository_id",
        dest="graph_repository_id",
        required=True,
        help="GraphDB repository id, for example qa_dataset",
    )

    return parser


def main():
    args_parser = get_args_parser()
    args = args_parser.parse_args()

    graph = GraphDB(
        base_url=args.graph_base_url,
        repository_id=args.graph_repository_id,
    )

    train_split, dev_split, _ = load_and_split_qa_dataset(Path(args.qa_dataset_path))

    split: list[dict] = train_split + dev_split
    max_limit = len([question for template in split for question in template["questions"]])
    min_limit = find_global_min_limit(graph, dev_split, max_limit)
    print(f"The minimum limit is {min_limit}")
