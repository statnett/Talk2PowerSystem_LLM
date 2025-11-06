import argparse
from pathlib import Path

from talk2powersystemllm.qa_dataset import load_and_split_qa_dataset, build_qa_dataset_graph


def get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serialize the train and dev splits of the Q&A dataset as turtle")
    parser.add_argument(
        "--qa-dataset-path",
        dest="qa_dataset_path",
        required=True,
        help="Path to the Q&A dataset serialized in the expected yaml format",
    )
    parser.add_argument(
        "--output_folder",
        dest="output_folder",
        required=True,
        help="Path to the output directory, where the turtle file will be serialized",
    )
    return parser


def main():
    args_parser = get_args_parser()
    args = args_parser.parse_args()

    train_split, dev_split, _ = load_and_split_qa_dataset(Path(args.qa_dataset_path))

    graph = build_qa_dataset_graph(train_split + dev_split)

    output_file = Path(args.output_folder) / "qa_dataset.trig"
    graph.serialize(
        output_file,
        format="trig",
        encoding="utf-8",
    )
