from datetime import datetime

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool, ToolException
from ttyg.utils import timeit

from talk2powersystemllm.tools.user_datetime_context import user_datetime_ctx


class NowTool(BaseTool):
    """
    Tool, which returns the user's current date time in yyyy-mm-ddTHH:MM:SS±hhmm format (ISO 8601).
    """

    name: str = "now"
    description: str = ("Returns the user's current date time in yyyy-mm-ddTHH:MM:SS±hhmm format (ISO 8601). "
                        "Do not reuse responses.")
    handle_tool_error: bool = True

    @timeit
    def _run(
        self,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        try:
            return user_datetime_ctx.get() or datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
        except Exception as e:
            raise ToolException(str(e))
