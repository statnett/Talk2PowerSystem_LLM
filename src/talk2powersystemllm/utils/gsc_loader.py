import random
from pathlib import Path

import yaml


def load_gsc(path: Path) -> tuple[list[dict], list[dict], list[dict]]:
    with open(path, "r", encoding="utf-8") as file:
        gsc: list[dict] = yaml.safe_load(file)

        # Check if template ids and question ids are unique
        template_ids = [template["template_id"] for template in gsc]
        assert len(template_ids) == len(set(template_ids)), "Templates ids are not unique!"
        questions_ids = [question["id"] for template in gsc for question in template["questions"]]
        assert len(questions_ids) == len(set(questions_ids)), "Questions ids are not unique!"

        # filter templates with no questions; we shouldn't have such, but for now they are present
        gsc = [t for t in gsc if len(t["questions"]) > 0]

        # random split train (80%) / dev (10%) / test (10%)
        random.seed(1)
        random.shuffle(gsc)

        train_split_index = int(len(gsc) * 0.80)
        dev_split_index = int(len(gsc) * 0.90)

        train_split = gsc[:train_split_index]
        dev_split = gsc[train_split_index:dev_split_index]
        test_split = gsc[dev_split_index:]

        return train_split, dev_split, test_split
