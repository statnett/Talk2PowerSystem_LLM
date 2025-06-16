from typing import Type

from cognite.client.data_classes import filters
from pydantic import BaseModel, Field
from ttyg.utils import timeit

from .base import BaseCogniteTool


class RetrieveTimeSeriesTool(BaseCogniteTool):
    """
    A tool, which retrieves time series.
    """

    class ArgumentsSchema(BaseModel):
        limit: int | None = Field(
            description="Maximum number of time series to return. "
                        "Defaults to 25. Set to `-1` to return all items. ",
            default=25,
        )
        mrid: str | list[str] | None = Field(
            description=(
                "Filter time series by one or more master resource IDs (mrid). "
                "Note: mrid is not the same as external_id."
                "Examples: a single mrid, e.g. '105384df-9b48-3848-8fd2-97cf37575885' or a list of multiple mrids, "
                "e.g. ['3916ae31-9f3d-af4e-8d87-87d373d8200a', 'fa58f41d-1ee2-9146-8dfc-4595cd86ed0e']"
            ),
            examples=[
                "105384df-9b48-3848-8fd2-97cf37575885",
                ["3916ae31-9f3d-af4e-8d87-87d373d8200a", "fa58f41d-1ee2-9146-8dfc-4595cd86ed0e"]
            ],
            default=None,
        )

    name: str = "retrieve_time_series"
    description: str = "Retrieve one or more time series. Optionally, the time series can be filtered by mrid."
    args_schema: Type[BaseModel] = ArgumentsSchema

    @timeit
    def _run(
            self,
            limit: int | None = 25,
            mrid: str | list[str] | None = None,
    ) -> str:
        advanced_filter = None
        if mrid is not None:
            if isinstance(mrid, str):
                advanced_filter = filters.Equals(["metadata", "mrid"], mrid)
            else:
                for idx, item in enumerate(mrid):
                    if idx == 0:
                        advanced_filter = filters.Equals(["metadata", "mrid"], item)
                    else:
                        advanced_filter = advanced_filter | filters.Equals(["metadata", "mrid"], item)

        return self.cognite_client.time_series.list(
            limit=limit,
            advanced_filter=advanced_filter
        )
