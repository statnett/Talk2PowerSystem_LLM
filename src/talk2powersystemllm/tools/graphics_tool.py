import logging
from typing import Literal, Tuple, Type
from urllib.parse import quote

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import ToolException
from pydantic import BaseModel, Field, model_validator
from pyparsing import ParseException
from rdflib import Variable
from rdflib.plugins.sparql import prepareQuery
from ttyg.tools import BaseArtifact, SparqlQueryTool
from ttyg.utils import timeit
from typing_extensions import Self

logger = logging.getLogger(__name__)


class GraphicArtifact(BaseArtifact):
    mime_type: str
    link: str


class SvgArtifact(GraphicArtifact):
    type: Literal["svg"] = "svg"


class GraphDBVisualGraphArtifact(GraphicArtifact):
    type: Literal["gdb_viz_graph"] = "gdb_viz_graph"


class GraphicsTool(SparqlQueryTool):
    """
    Displays a diagram specified by its IRI or
    a diagram specified by IRI of a diagram configuration and node IRI
    """

    class ArgumentsSchema(BaseModel):
        diagram_iri: str | None = Field(
            description="The IRI of a diagram. "
            "Pass `diagram_iri` or `diagram_configuration_iri`, but not both.",
            default=None,
        )
        diagram_configuration_iri: str | None = Field(
            description="The IRI of a diagram configuration. "
            "Pass `diagram_iri` or `diagram_configuration_iri`, but not both. "
            "When passing `diagram_configuration_iri`, argument `node_iri` is also required.",
            default=None,
        )
        node_iri: str | None = Field(
            description="The IRI of a node. "
            "When passing `node_iri`, argument `diagram_configuration_iri` is also required.",
            default=None,
        )

    name: str = "display_graphics"
    description: str = (
        "Displays a diagram specified by its IRI or "
        "a diagram specified by IRI of a diagram configuration and node IRI"
    )
    sparql_query_template: str = """PREFIX dct: <http://purl.org/dc/terms/>
PREFIX cimd: <https://cim.ucaiug.io/diagrams#>
PREFIX cim: <https://cim.ucaiug.io/ns#>
SELECT ?link ?name ?format ?description ?kind {{
    <{iri}> cimd:Diagram.link|cimd:DiagramConfiguration.link ?link;
        cim:IdentifiedObject.name ?name;
        dct:format ?format.
    OPTIONAL {{
        <{iri}> cimd:Diagram.kind / rdfs:label ?kind
    }}
    OPTIONAL {{
        <{iri}> cim:IdentifiedObject.description ?description
    }}
}}"""
    args_schema: Type[BaseModel] = ArgumentsSchema

    @model_validator(mode="after")
    def validate_sparql_query_template(self) -> Self:
        """
        Validate the SPARQL query template uses SELECT
        """

        try:
            parsed_query = prepareQuery(
                self.sparql_query_template.format(iri="http://example.com/")
            )
        except ParseException as e:
            raise ValueError("Graphics tool SPARQL query template is not valid.", e)

        if parsed_query.algebra.name != "SelectQuery":
            raise ValueError("Invalid query type. Only SELECT queries are supported.")

        return self

    @timeit
    def _run(
        self,
        diagram_iri: str | None,
        diagram_configuration_iri: str | None,
        node_iri: str | None,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> Tuple[str, SvgArtifact | GraphDBVisualGraphArtifact | None]:
        if (not diagram_iri) and (not diagram_configuration_iri):
            raise ValueError(
                "One of `diagram_iri` or `diagram_configuration_iri` arguments must be provided!"
            )
        if diagram_iri and diagram_configuration_iri:
            raise ValueError(
                "Only one of `diagram_iri` and `diagram_configuration_iri` arguments "
                "must be provided, not both!"
            )
        if diagram_configuration_iri and (not node_iri):
            raise ValueError(
                "When passing `diagram_configuration_iri`, argument `node_iri` is also required."
            )

        query = self.sparql_query_template.format(
            iri=diagram_iri if diagram_iri else diagram_configuration_iri,
        )
        logger.debug(f"Fetching diagram with query {query}")
        try:
            query_results, _ = self.graph.eval_sparql_query(
                self.graphdb_repository_id, query
            )
            if len(query_results.bindings) > 0:
                bindings = query_results.bindings[0]
                name = bindings[Variable("name")].value
                format_ = bindings[Variable("format")].value

                link = bindings[Variable("link")].value
                if diagram_configuration_iri:
                    link += f"&uri={quote(node_iri)}"

                if format_ == "image/svg+xml":
                    artifact = SvgArtifact(link=quote(link), mime_type=format_)
                elif format_ == "text/html":
                    artifact = GraphDBVisualGraphArtifact(
                        link=f"{link}&embedded=true", mime_type=format_
                    )
                else:
                    logger.warning(f"Found a diagram with unknown format {format_}")
                    return (
                        f"Found a diagram with unknown format {format_}. Can't render it!",
                        None,
                    )

                content = f'Diagram with name "{name}"'
                if Variable("description") in bindings:
                    content += (
                        f' and description "{bindings[Variable("description")].value}"'
                    )
                if Variable("kind") in bindings:
                    content += f' of kind "{bindings[Variable("kind")].value}"'
                if diagram_configuration_iri:
                    content += f' for "{node_iri}"'
                return content, artifact

            else:
                return "No diagram found", None

        except Exception as e:
            raise ToolException(str(e))
