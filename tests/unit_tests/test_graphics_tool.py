from unittest.mock import MagicMock

import httpx
import pytest
from langchain_core.tools import ToolException
from rdflib import Literal as RDFLiteral
from rdflib import Variable
from ttyg.graphdb import GraphDB

from talk2powersystemllm.tools import (
    GraphDBVisualGraphArtifact,
    GraphicsTool,
    SvgArtifact,
)


class MockBindings:
    def __init__(self, data):
        self.bindings = [data] if data else []


@pytest.fixture
def mock_graphdb() -> MagicMock:
    return MagicMock(spec=GraphDB)


@pytest.fixture
def graphics_tool(mock_graphdb) -> GraphicsTool:
    return GraphicsTool(graph=mock_graphdb, graphdb_repository_id="cim")


def test_graphics_tool_svg(graphics_tool: GraphicsTool, mock_graphdb: GraphDB) -> None:
    mock_results = MockBindings(
        {
            Variable("name"): RDFLiteral("Diagram of substation OSLO"),
            Variable("format"): RDFLiteral("image/svg+xml"),
            Variable("link"): RDFLiteral("PowSyBl-SLD-substation-OSLO.svg"),
            Variable("description"): RDFLiteral(
                "PowSyBl Single-Line-Diagram of substation OSLO"
            ),
            Variable("kind"): RDFLiteral("PowSyBl-SingleLineDiagram"),
        }
    )
    mock_graphdb.eval_sparql_query.return_value = (mock_results, None)

    content, artifact = graphics_tool._run(
        diagram_iri="urn:uuid:a53f9c60-189d-4be2-b3af-0320298e529d",
        diagram_configuration_iri=None,
        node_iri=None,
    )

    assert isinstance(artifact, SvgArtifact)
    assert artifact.link == "PowSyBl-SLD-substation-OSLO.svg"
    assert artifact.mime_type == "image/svg+xml"
    assert content == (
        'Diagram with name "Diagram of substation OSLO" and description '
        '"PowSyBl Single-Line-Diagram of substation OSLO" of kind '
        '"PowSyBl-SingleLineDiagram"'
    )
    assert mock_graphdb.eval_sparql_query.call_count == 1


def test_graphics_tool_viz_graph_with_node(
    graphics_tool: GraphicsTool, mock_graphdb: GraphDB
) -> None:
    mock_results = MockBindings(
        {
            Variable("name"): RDFLiteral("Class hierarchy (VizGraph config)"),
            Variable("format"): RDFLiteral("text/html"),
            Variable("link"): RDFLiteral(
                "graphs-visualizations?config=5099ad5fc1954153a12f1f052fe1df7c"
            ),
            Variable("description"): RDFLiteral(
                "Shows the hierarchy (parent and children) of any class."
            ),
        }
    )
    mock_graphdb.eval_sparql_query.return_value = (mock_results, None)

    content, artifact = graphics_tool._run(
        diagram_iri=None,
        diagram_configuration_iri="urn:uuid:e81beed4-781c-4683-91a4-9ed8d8ebf377",
        node_iri="https://cim.ucaiug.io/ns#Equipment",
    )

    assert isinstance(artifact, GraphDBVisualGraphArtifact)
    assert artifact.link == (
        "graphs-visualizations?config=5099ad5fc1954153a12f1f052fe1df7c"
        "&uri=https%3A//cim.ucaiug.io/ns%23Equipment&embedded=true"
    )
    assert artifact.mime_type == "text/html"
    assert content == (
        'Diagram with name "Class hierarchy (VizGraph config)" and description '
        '"Shows the hierarchy (parent and children) of any class." for '
        '"https://cim.ucaiug.io/ns#Equipment"'
    )
    assert mock_graphdb.eval_sparql_query.call_count == 1


def test_graphics_tool_no_results(
    graphics_tool: GraphicsTool, mock_graphdb: GraphDB
) -> None:
    mock_graphdb.eval_sparql_query.return_value = (MockBindings(None), None)

    content, artifact = graphics_tool._run(
        diagram_iri=None,
        diagram_configuration_iri="urn:uuid:e81beed4-781c-4683-91a4-9ed8d8ebf378",
        node_iri="https://cim.ucaiug.io/ns#Equipment",
    )

    assert artifact is None
    assert content == "No diagram found"
    assert mock_graphdb.eval_sparql_query.call_count == 1


def test_graphics_tool_unknown_format(
    graphics_tool: GraphicsTool, mock_graphdb: GraphDB
) -> None:
    mock_results = MockBindings(
        {
            Variable("name"): RDFLiteral("Diagram of substation OSLO"),
            Variable("format"): RDFLiteral("image/jpeg"),
            Variable("link"): RDFLiteral("PowSyBl-SLD-substation-OSLO.svg"),
            Variable("description"): RDFLiteral(
                "PowSyBl Single-Line-Diagram of substation OSLO"
            ),
            Variable("kind"): RDFLiteral("PowSyBl-SingleLineDiagram"),
        }
    )
    mock_graphdb.eval_sparql_query.return_value = (mock_results, None)

    content, artifact = graphics_tool._run(
        diagram_iri="urn:uuid:a53f9c60-189d-4be2-b3af-0320298e529d",
        diagram_configuration_iri=None,
        node_iri=None,
    )

    assert artifact is None
    assert content == "Found a diagram with unknown format image/jpeg. Can't render it!"
    assert mock_graphdb.eval_sparql_query.call_count == 1


def test_graphics_tool_validation_errors(graphics_tool: GraphicsTool) -> None:
    with pytest.raises(
        ValueError,
        match="One of `diagram_iri` or `diagram_configuration_iri` arguments must be provided!",
    ):
        graphics_tool._run(
            diagram_iri=None,
            diagram_configuration_iri=None,
            node_iri=None,
        )

    with pytest.raises(
        ValueError,
        match="Only one of `diagram_iri` and `diagram_configuration_iri` arguments "
        "must be provided, not both!",
    ):
        graphics_tool._run(
            diagram_iri="urn:uuid:a53f9c60-189d-4be2-b3af-0320298e529d",
            diagram_configuration_iri="urn:uuid:e81beed4-781c-4683-91a4-9ed8d8ebf377",
            node_iri=None,
        )

    with pytest.raises(
        ValueError,
        match="When passing `diagram_configuration_iri`, argument `node_iri` is also required.",
    ):
        graphics_tool._run(
            diagram_iri=None,
            diagram_configuration_iri="urn:uuid:e81beed4-781c-4683-91a4-9ed8d8ebf377",
            node_iri=None,
        )


def test_validate_sparql_query_template_success(mock_graphdb: GraphDB) -> None:
    valid_query = "SELECT ?p ?o WHERE {{ <{iri}> ?p ?o }}"

    tool = GraphicsTool(
        sparql_query_template=valid_query,
        graph=mock_graphdb,
        graphdb_repository_id="cim",
    )

    assert tool.sparql_query_template == valid_query


def test_validate_sparql_query_template_invalid_syntax(mock_graphdb: GraphDB) -> None:
    invalid_syntax = "SELECT ?s WHERE {{ <{iri}> ?p ?o"

    with pytest.raises(
        ValueError,
        match="Graphics tool SPARQL query template is not valid.",
    ):
        GraphicsTool(
            sparql_query_template=invalid_syntax,
            graph=mock_graphdb,
            graphdb_repository_id="cim",
        )


def test_validate_sparql_query_template_wrong_type(mock_graphdb: GraphDB) -> None:
    ask_query = "ASK WHERE {{ <{iri}> ?p ?o }}"

    with pytest.raises(
        ValueError,
        match="Invalid query type. Only SELECT queries are supported.",
    ):
        GraphicsTool(
            sparql_query_template=ask_query,
            graph=mock_graphdb,
            graphdb_repository_id="cim",
        )


def test_graphics_tool_eval_sparql_query_error(
    graphics_tool: GraphicsTool, mock_graphdb: GraphDB
) -> None:
    mock_graphdb.eval_sparql_query.side_effect = httpx.TimeoutException("Timeout error")

    with pytest.raises(
        ToolException,
        match="Timeout error",
    ):
        graphics_tool._run(
            diagram_iri="urn:uuid:a53f9c60-189d-4be2-b3af-0320298e529d",
            diagram_configuration_iri=None,
            node_iri=None,
        )

    assert mock_graphdb.eval_sparql_query.call_count == 1
