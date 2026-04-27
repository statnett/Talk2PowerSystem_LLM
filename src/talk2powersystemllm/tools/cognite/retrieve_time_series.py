from typing import Type

from cognite.client.data_classes import filters
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import ToolException
from pydantic import BaseModel, Field
from ttyg.utils import timeit

from talk2powersystemllm.tools.cognite.base import BaseCogniteTool


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
        rndp_mrid: str | list[str] | None = Field(
            description=(
                "Filter time series by one or more master resource IDs (mrid). "
                "Note: RNDP_mrid is not the same as external_id."
                "Examples: a single mrid, e.g. '105384df-9b48-3848-8fd2-97cf37575885' "
                "or a list of multiple mrids, e.g. "
                "['3916ae31-9f3d-af4e-8d87-87d373d8200a', 'fa58f41d-1ee2-9146-8dfc-4595cd86ed0e']"
            ),
            examples=[
                "105384df-9b48-3848-8fd2-97cf37575885",
                [
                    "3916ae31-9f3d-af4e-8d87-87d373d8200a",
                    "fa58f41d-1ee2-9146-8dfc-4595cd86ed0e",
                ],
            ],
            default=None,
        )

    name: str = "retrieve_time_series"
    description: str = (
        "Retrieve one or more time series. Optionally, the time series can be filtered by RNDP_mrid "
        "to fetch the corresponding external_id."
    )
    args_schema: Type[BaseModel] = ArgumentsSchema

    @timeit
    def _run(
        self,
        limit: int | None = 25,
        rndp_mrid: str | list[str] | None = None,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        try:
            exists_filter = filters.Exists(["metadata", "RNDP_mrid"])
            advanced_filter = exists_filter

            if rndp_mrid is not None:
                if isinstance(rndp_mrid, str):
                    mrid_filter = filters.Equals(["metadata", "RNDP_mrid"], rndp_mrid)
                else:
                    mrid_filter = filters.In(["metadata", "RNDP_mrid"], rndp_mrid)
                advanced_filter = exists_filter & mrid_filter

            return self.cognite_session.client().time_series.list(
                limit=limit, advanced_filter=advanced_filter
            )
        except Exception as e:
            raise ToolException(str(e))
