from ttyg.utils import timeit

from .base import BaseCogniteTool


class ListTimeSeriesTool(BaseCogniteTool):
    name: str = "list_time_series"
    description: str = "List time series"

    @timeit
    def _run(
            self,
    ) -> str:
        return self.cognite_client.time_series.list(
            limit=None,
        )
