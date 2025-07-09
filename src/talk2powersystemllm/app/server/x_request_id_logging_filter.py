import logging

from .main import ctx_request


class XRequestIdFilter(logging.Filter):
    def filter(self, record) -> bool:
        request = ctx_request.get()
        record.x_request_id = request
        return True
