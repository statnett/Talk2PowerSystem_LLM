import random
from pathlib import Path

import yaml


def load_and_split_qa_dataset(path_to_yaml: Path) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Loads the Q&A dataset, shuffles it, and splits it into 3 parts: train(80%), dev(10%) and test(10%).
    """
    with open(path_to_yaml, "r", encoding="utf-8") as yaml_file:
        qa_dataset: list[dict] = yaml.safe_load(yaml_file)

        # Check if template ids and question ids are unique
        template_ids = [template["template_id"] for template in qa_dataset]
        assert len(template_ids) == len(set(template_ids)), "Templates ids are not unique!"
        questions_ids = [question["id"] for template in qa_dataset for question in template["questions"]]
        assert len(questions_ids) == len(set(questions_ids)), "Questions ids are not unique!"

        # filter templates with no questions; we shouldn't have such, but for now they are present
        qa_dataset = [t for t in qa_dataset if len(t["questions"]) > 0]

        random.seed(1)
        random.shuffle(qa_dataset)

        train_split_index = int(len(qa_dataset) * 0.80)
        dev_split_index = int(len(qa_dataset) * 0.90)

        train_split = qa_dataset[:train_split_index]
        dev_split = qa_dataset[train_split_index:dev_split_index]
        test_split = qa_dataset[dev_split_index:]

        return train_split, dev_split, test_split
