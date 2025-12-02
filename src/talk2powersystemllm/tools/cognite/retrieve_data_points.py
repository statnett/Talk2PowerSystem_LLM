import datetime
from typing import Type

from cognite.client.data_classes.datapoints import Aggregate, DatapointsArray, DatapointsArrayList
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import ToolException
from pydantic import BaseModel, Field
from ttyg.utils import timeit

from .base import BaseCogniteTool


class RetrieveDataPointsTool(BaseCogniteTool):
    """
    A tool, which retrieves datapoints for one or more time series.
    Supported arguments: `external_id`, `limit`, `start`, `end`, `aggregates` and `granularity`.
    """

    class ArgumentsSchema(BaseModel):
        external_id: str | list[str] = Field(description="One or more external IDs")
        limit: int | None = Field(
            description="Maximum number of datapoints to return for each time series. "
                        "By default no limit is applied. For aggregates no limit must be applied. "
                        "If `start` or `end` are used to filter the data points for a short period of time, "
                        "no limit must be applied. If there are no aggregates or the time period is a long one, "
                        "and even if the user asks for `all` data points, a default limit of 10 must be applied. ",
            ge=0,
            default=None
        )
        start: str | None = Field(
            description="Get datapoints starting from, and including, this time. "
                        "The format is either ISO 8601 (in UTC time), or "
                        "``<positive-integer>(s|m|h|d|w)-(ago|ahead)``, where ``s`` is short for ``seconds``, "
                        "``m`` is short for ``minutes``, ``h`` is short for ``hours``, ``d`` is short for ``days``, "
                        "and ``w`` is short for ``weeks``. "
                        "Example: ``2d-ago`` gets datapoints that are up to 2 days old. "
                        "Note that for aggregates, the start time is rounded down to a whole granularity unit "
                        "(in UTC timezone). "
                        "Daily granularities (d) are rounded to 0:00 AM; hourly granularities (h) to the start of "
                        "the hour, etc. "
                        "Argument ``end`` must be later than argument ``start``.",
            examples=[
                "3w-ago",
                "3h-ahead",
                "2025-06-04",
                "2025-06-04T14",
                "2025-06-04T14:30",
                "2025-06-04T14:30:30",
                "2025-06-04T14:30:30.123",
                "2025-06-04T14:30:30Z",
                "2025-06-04T14:30:30.123Z",
                "2025-06-04T14:30:30-04:00",
                "2025-06-04T14:30:30.123-04:00",
                "2025-06-04T14:30:30-0400",
                "2025-06-04T14:30:30.123-0400",
                "2025-06-04T14:30:30-04",
                "2025-06-04T14:30:30.123-04",
            ],
            default=None
        )
        end: str | None = Field(
            description="Get datapoints up to, but excluding, this point in time. "
                        "The format is ISO 8601 (in UTC time), or ``now``, or "
                        "``<positive-integer>(s|m|h|d|w)-(ago|ahead)``, where ``s`` is short for ``seconds``, "
                        "``m`` is short for ``minutes``, ``h`` is short for ``hours``, ``d`` is short for ``days``, "
                        "and ``w`` is short for ``weeks``. "
                        "Note that when using aggregates, the end will be rounded up such that the last aggregate "
                        "represents a full aggregation interval containing the original end, "
                        "where the interval is the granularity unit times the granularity multiplier. "
                        "For granularity ``2d``, the aggregation interval is 2 days, if end was originally 3 days after "
                        "the start, it will be rounded to 4 days after the start. "
                        "Argument ``end`` must be later than argument ``start``. "
                        "By default ``end`` is ``now``. ",
            examples=[
                "3w-ago",
                "3h-ahead",
                "now",
                "2025-06-04",
                "2025-06-04T14",
                "2025-06-04T14:30",
                "2025-06-04T14:30:30",
                "2025-06-04T14:30:30.123",
                "2025-06-04T14:30:30Z",
                "2025-06-04T14:30:30.123Z",
                "2025-06-04T14:30:30-04:00",
                "2025-06-04T14:30:30.123-04:00",
                "2025-06-04T14:30:30-0400",
                "2025-06-04T14:30:30.123-0400",
                "2025-06-04T14:30:30-04",
                "2025-06-04T14:30:30.123-04",
            ],
            default=None
        )
        aggregates: Aggregate | list[Aggregate] | None = Field(
            description="The aggregates to return. When passing `aggregates`, argument `granularity` is also required.",
            default=None,
            examples=["average", ["average", "count"]]
        )
        granularity: str | None = Field(
            description="The time granularity size and unit to aggregate over. "
                        "For example, a granularity '5m' means that aggregates are calculated over 5 minutes. "
                        "The unit can be given as an abbreviation or spelled out for clarity: "
                        "``s/second(s)``, ``m/minute(s)``, ``h/hour(s)``, ``d/day(s)``, "
                        "``w/week(s)``, ``mo/month(s)``, ``q/quarter(s)``, or ``y/year(s)``. "
                        "Examples: ``30s``, ``5m``, ``1day``, ``2weeks``. "
                        "For 'second' and 'minute', the multiple must be an integer between 1 and 120 inclusive. "
                        "For 'hour', 'day', and 'month', the multiple must be an integer between 1 and 100000 inclusive. "
                        "When passing `granularity`, argument `aggregates` is also required.",
            default=None,
            examples=["1w", "1mo", "2days"]
        )

    name: str = "retrieve_data_points"
    description: str = "Retrieve datapoints for one or more time series"
    args_schema: Type[BaseModel] = ArgumentsSchema

    @timeit
    def _run(
        self,
        external_id: str | list[str],
        limit: int | None = None,
        start: str | None = None,
        end: str | None = None,
        aggregates: Aggregate | list[Aggregate] | None = None,
        granularity: str | None = None,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> DatapointsArray | DatapointsArrayList | None:
        try:
            start = self._try_to_parse_as_iso_format(start)
            end = self._try_to_parse_as_iso_format(end)
            return self.cognite_session.client().time_series.data.retrieve_arrays(
                external_id=external_id,
                limit=limit,
                start=start,
                end=end,
                aggregates=aggregates,
                granularity=granularity,
            )
        except Exception as e:
            raise ToolException(str(e))

    @staticmethod
    def _try_to_parse_as_iso_format(datetime_string: str | None) -> str | datetime.datetime | None:
        if datetime_string is None:
            return None

        try:
            dt = datetime.datetime.fromisoformat(datetime_string)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt.astimezone(datetime.timezone.utc)
        except ValueError:
            # Probably the LLM wants to use the time shift format (e.g., `1h-ago`)
            return datetime_string
