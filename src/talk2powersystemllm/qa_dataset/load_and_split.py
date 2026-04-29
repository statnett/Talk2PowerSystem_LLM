import random
from pathlib import Path

import yaml


def load_qa_dataset(
    path_to_yaml: Path,
) -> list[dict]:
    """
    Loads the Q&A dataset
    """
    with open(path_to_yaml, "r", encoding="utf-8") as yaml_file:
        qa_dataset: list[dict] = yaml.safe_load(yaml_file)

        # filter templates with no questions; we shouldn't have such, but for now they are present
        qa_dataset = [t for t in qa_dataset if len(t["questions"]) > 0]

        # Check if template ids and question ids are unique
        template_ids = [template["template_id"] for template in qa_dataset]
        assert len(template_ids) == len(set(template_ids)), (
            "Templates ids are not unique!"
        )
        questions_ids = [
            question["id"]
            for template in qa_dataset
            for question in template["questions"]
        ]
        assert len(questions_ids) == len(set(questions_ids)), (
            "Questions ids are not unique!"
        )

        return qa_dataset


def load_and_split_qa_dataset(
    path_to_yaml: Path,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Loads the Q&A dataset, shuffles it, and splits it into 3 parts: train, dev and test.
    The size of the dev and test splits is 10% .
    The remaining templates are in the train split.
    """
    qa_dataset = load_qa_dataset(path_to_yaml)

    random.seed(1)
    random.shuffle(qa_dataset)

    dev_test_size = int(len(qa_dataset) * 0.1)

    test_split = qa_dataset[:dev_test_size]
    dev_split = qa_dataset[dev_test_size : (2 * dev_test_size)]
    train_split = qa_dataset[(2 * dev_test_size) :]

    return train_split, dev_split, test_split
