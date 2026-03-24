from unittest.mock import MagicMock

from fastapi import Request

from talk2powersystemllm.app.server.routers.chat import (
    build_diagram_image_url,
    build_gdb_visual_graph_url,
)


def test_build_gdb_visual_graph_url_with_trailing_slash() -> None:
    mock_factory = MagicMock()
    mock_factory.graphdb_base_url = "https://cim.ontotext.com/graphdb/"
    link = (
        "graphs-visualizations?config=5099ad5fc1954153a12f1f052fe1df7c"
        "&uri=https%3A//cim.ucaiug.io/ns%23Equipment&embedded=true"
    )

    result = build_gdb_visual_graph_url(mock_factory, link)

    assert (
        result == "https://cim.ontotext.com/graphdb/graphs-visualizations"
        "?config=5099ad5fc1954153a12f1f052fe1df7c"
        "&uri=https%3A//cim.ucaiug.io/ns%23Equipment&embedded=true"
    )


def test_build_gdb_visual_graph_url_without_trailing_slash() -> None:
    mock_factory = MagicMock()
    mock_factory.graphdb_base_url = "https://cim.ontotext.com/graphdb"
    link = (
        "graphs-visualizations?config=5099ad5fc1954153a12f1f052fe1df7c"
        "&uri=https%3A//cim.ucaiug.io/ns%23Equipment&embedded=true"
    )

    result = build_gdb_visual_graph_url(mock_factory, link)

    assert (
        result == "https://cim.ontotext.com/graphdb/graphs-visualizations"
        "?config=5099ad5fc1954153a12f1f052fe1df7c"
        "&uri=https%3A//cim.ucaiug.io/ns%23Equipment&embedded=true"
    )


def test_build_diagram_image_url_with_context_path() -> None:
    mock_request = MagicMock(spec=Request)
    mock_request.app.state.settings.frontend_context_path = "/chat"
    mock_request.app.url_path_for.return_value = (
        "/rest/chat/diagrams/PowSyBl-SLD-substation-OSLO.svg"
    )

    result = build_diagram_image_url(mock_request, "PowSyBl-SLD-substation-OSLO.svg")

    assert result == "/chat/rest/chat/diagrams/PowSyBl-SLD-substation-OSLO.svg"
    mock_request.app.url_path_for.assert_called_with(
        "diagrams", filename="PowSyBl-SLD-substation-OSLO.svg"
    )


def test_build_diagram_image_url_root_context() -> None:
    mock_request = MagicMock(spec=Request)
    mock_request.app.state.settings.frontend_context_path = "/"
    mock_request.app.url_path_for.return_value = (
        "/rest/chat/diagrams/PowSyBl-SLD-substation-OSLO.svg"
    )

    result = build_diagram_image_url(mock_request, "PowSyBl-SLD-substation-OSLO.svg")

    assert result == "/rest/chat/diagrams/PowSyBl-SLD-substation-OSLO.svg"
