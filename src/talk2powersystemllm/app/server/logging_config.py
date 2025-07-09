import logging.config as logging_config
from pathlib import Path

import yaml


class LoggingConfig:

    @staticmethod
    def config_logger(logging_yaml: Path) -> None:
        with open(logging_yaml, "r") as f:
            config = yaml.safe_load(f.read())
            logging_config.dictConfig(config)
