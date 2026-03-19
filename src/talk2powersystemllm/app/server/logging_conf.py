import logging
import logging.config as logging_config
from pathlib import Path

import yaml

from talk2powersystemllm.app.server.middleware import CTX_REQUEST


def config_logger(logging_yaml: Path) -> None:
    with open(logging_yaml, "r") as f:
        config = yaml.safe_load(f.read())
        logging_config.dictConfig(config)


class XRequestIdFilter(logging.Filter):
    def filter(self, record) -> bool:
        request = CTX_REQUEST.get()
        record.x_request_id = request
        return True
