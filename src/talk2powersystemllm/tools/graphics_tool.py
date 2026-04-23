import logging
from typing import Type, Tuple, Literal

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import ToolException
from pydantic import BaseModel, Field
from ttyg.tools import BaseArtifact, BaseGraphDBTool
from ttyg.utils import timeit


class ImageArtifact(BaseArtifact):
    type: Literal["image"] = "image"
    mime_type: str
    data: str


class GraphicsTool(BaseGraphDBTool):
    """
    Returns the diagram specified by the IRI
    """

    class ArgumentsSchema(BaseModel):
        iri: str = Field(description="The IRI of the diagram")

    name: str = "display_graphics"
    description: str = "Returns the diagram specified by the IRI"
    sparql_query_template: str = """PREFIX dct: <http://purl.org/dc/terms/>
PREFIX cimd: <https://cim.ucaiug.io/diagrams#>
PREFIX cim: <https://cim.ucaiug.io/ns#>
SELECT ?link ?name ?description ?format {{
    <{iri}> cimd:Diagram.link ?link;
        cim:IdentifiedObject.name ?name;
        cim:IdentifiedObject.description ?description;
        dct:format ?format.
}}"""
    args_schema: Type[BaseModel] = ArgumentsSchema
    response_format: str = "content_and_artifact"

    @timeit
    def _run(
        self,
        iri: str,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> Tuple[str, ImageArtifact | None]:
        query = self.sparql_query_template.format(
            iri=iri,
        )
        logging.debug(f"Fetching diagram with query {query}")
        try:
            query_results, _ = self.graph.eval_sparql_query(query)
            if len(query_results["results"]["bindings"]) > 0:
                link = query_results["results"]["bindings"][0]["link"]["value"]
                name = query_results["results"]["bindings"][0]["name"]["value"]
                description = query_results["results"]["bindings"][0]["description"]["value"]
                format_ = query_results["results"]["bindings"][0]["format"]["value"]
                return f"Diagram with name \"{name}\" and description \"{description}\"", ImageArtifact(
                    data=link,
                    mime_type=format_
                )
            else:
                return "No diagram", None
        except Exception as e:
            raise ToolException(str(e))
