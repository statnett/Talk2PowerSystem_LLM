from unittest.mock import MagicMock

import pytest
from rdflib.contrib.graphdb.exceptions import (
    RepositoryNotFoundError,
    RepositoryNotHealthyError,
)
from ttyg.graphdb import GraphDBRdfRankStatus, GraphDBAutocompleteStatus

from talk2powersystemllm.app.models import HealthStatus
from talk2powersystemllm.app.server.services.healthchecks import GraphDBHealthchecker

# minimal responses
green_status = {
    "status": "green"
}
yellow_status = {
    "status": "yellow"
}
red_status = {
    "status": "red"
}
green_status_with_connector = {
    "status": "green",
    "components": [
        {
            "name": "plugins",
            "components": [
                {
                    "name": "chatgpt-retrieval-connector",
                    "components": [
                        {
                            "name": "qa_dataset",
                            "status": "green"
                        }
                    ]
                }
            ]
        }
    ]
}
green_status_with_yellow_connector = {
    "status": "green",
    "components": [
        {
            "name": "plugins",
            "components": [
                {
                    "name": "chatgpt-retrieval-connector",
                    "components": [
                        {
                            "name": "qa_dataset",
                            "status": "yellow"
                        }
                    ]
                }
            ]
        }
    ]
}
green_status_with_red_connector = {
    "status": "green",
    "components": [
        {
            "name": "plugins",
            "components": [
                {
                    "name": "chatgpt-retrieval-connector",
                    "components": [
                        {
                            "name": "qa_dataset",
                            "status": "red"
                        }
                    ]
                }
            ]
        }
    ]
}


@pytest.fixture(autouse=True)
def reset_singleton():
    """Clears the singleton instance before each test."""
    GraphDBHealthchecker._instances = {}
    yield


@pytest.fixture
def mock_agent_factory() -> MagicMock:
    factory = MagicMock()
    # Setup default basic repository info
    factory.graphdb_client = MagicMock()
    factory.graphdb_repository_id = "cim"

    # Setup default settings (no retrieval tool by default)
    factory.settings.tools.retrieval_search = None
    return factory


@pytest.mark.asyncio
async def test_success(mock_agent_factory: MagicMock) -> None:
    client = mock_agent_factory.graphdb_client
    client.health.return_value.json.return_value = green_status
    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.OK
    assert "GraphDB can be queried, the setup is correct, and the state is healthy." == result.message
    assert client.eval_sparql_query.call_count == 1
    assert client.get_autocomplete_status.call_count == 1
    assert client.get_rdf_rank_status.call_count == 1


@pytest.mark.asyncio
async def test_not_healthy_error(mock_agent_factory: MagicMock) -> None:
    client = mock_agent_factory.graphdb_client
    client.health.side_effect = RepositoryNotHealthyError("Repository cim is not healthy. 500 - Not healthy")

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert "Repository cim is not healthy. 500 - Not healthy" == result.message
    assert client.eval_sparql_query.call_count == 0
    assert client.get_autocomplete_status.call_count == 0
    assert client.get_rdf_rank_status.call_count == 0


@pytest.mark.asyncio
async def test_repository_not_found_error(mock_agent_factory: MagicMock) -> None:
    client = mock_agent_factory.graphdb_client
    client.health.side_effect = RepositoryNotFoundError("Repository cim not found.")

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert "Repository cim not found." == result.message
    assert client.eval_sparql_query.call_count == 0
    assert client.get_autocomplete_status.call_count == 0
    assert client.get_rdf_rank_status.call_count == 0


@pytest.mark.asyncio
async def test_red_repository(mock_agent_factory: MagicMock) -> None:
    client = mock_agent_factory.graphdb_client
    client.health.return_value.json.return_value = red_status

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert "GraphDB repository \"cim\" health status is red!" == result.message
    assert client.eval_sparql_query.call_count == 0
    assert client.get_autocomplete_status.call_count == 0
    assert client.get_rdf_rank_status.call_count == 0


@pytest.mark.asyncio
async def test_yellow_repository(mock_agent_factory: MagicMock) -> None:
    client = mock_agent_factory.graphdb_client
    client.health.return_value.json.return_value = yellow_status

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.WARNING
    assert "GraphDB repository \"cim\" health status is yellow!" == result.message
    assert client.eval_sparql_query.call_count == 0
    assert client.get_autocomplete_status.call_count == 0
    assert client.get_rdf_rank_status.call_count == 0


@pytest.mark.asyncio
async def test_eval_ask_query_exception(mock_agent_factory: MagicMock) -> None:
    client = mock_agent_factory.graphdb_client
    client.health.return_value.json.return_value = green_status

    error_message = "Some exception"
    client.eval_sparql_query.side_effect = Exception(error_message)

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert "Some exception" == result.message
    assert client.get_autocomplete_status.call_count == 0
    assert client.get_rdf_rank_status.call_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("autocomplete_status", [
    GraphDBAutocompleteStatus.READY_CONFIG,
    GraphDBAutocompleteStatus.ERROR,
    GraphDBAutocompleteStatus.NONE,
    GraphDBAutocompleteStatus.BUILDING,
    GraphDBAutocompleteStatus.CANCELED,
])
async def test_autocomplete_warning(
    mock_agent_factory: MagicMock,
    autocomplete_status: GraphDBAutocompleteStatus,
) -> None:
    client = mock_agent_factory.graphdb_client
    client.health.return_value.json.return_value = green_status

    client.get_autocomplete_status.return_value = autocomplete_status

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.WARNING
    assert (f"The Autocomplete index status of the repository is \"{autocomplete_status.name}\". "
            "It should be \"READY\".") == result.message
    assert client.get_rdf_rank_status.call_count == 0


@pytest.mark.asyncio
async def test_autocomplete_error(mock_agent_factory: MagicMock) -> None:
    client = mock_agent_factory.graphdb_client
    client.health.return_value.json.return_value = green_status

    error_message = "Some exception"
    client.get_autocomplete_status.side_effect = Exception(error_message)

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert "Some exception" == result.message
    assert client.get_rdf_rank_status.call_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("rdf_rank_status", [
    GraphDBRdfRankStatus.CANCELED,
    GraphDBRdfRankStatus.COMPUTING,
    GraphDBRdfRankStatus.EMPTY,
    GraphDBRdfRankStatus.ERROR,
    GraphDBRdfRankStatus.OUTDATED,
    GraphDBRdfRankStatus.CONFIG_CHANGED,
])
async def test_rdf_rank_warning(
    mock_agent_factory: MagicMock,
    rdf_rank_status: GraphDBRdfRankStatus,
) -> None:
    client = mock_agent_factory.graphdb_client
    client.health.return_value.json.return_value = green_status

    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = rdf_rank_status

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.WARNING
    assert (f"The RDF Rank status of the repository is \"{rdf_rank_status.name}\". "
            "It should be \"COMPUTED\".") == result.message
    assert client.get_autocomplete_status.call_count == 1


@pytest.mark.asyncio
async def test_rdf_rank_error(mock_agent_factory: MagicMock) -> None:
    client = mock_agent_factory.graphdb_client
    client.health.return_value.json.return_value = green_status

    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    error_message = "Some exception"
    client.get_rdf_rank_status.side_effect = Exception(error_message)

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert "Some exception" == result.message
    assert client.get_autocomplete_status.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_ok_same_repository(mock_agent_factory: MagicMock) -> None:
    retrieval_mock = MagicMock()
    retrieval_mock.graphdb_repository_id = "cim"
    retrieval_mock.connector_name = "qa_dataset"
    mock_agent_factory.settings.tools.retrieval_search = retrieval_mock

    client = mock_agent_factory.graphdb_client

    client.health.return_value.json.return_value = green_status_with_connector
    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.OK
    assert "GraphDB can be queried, the setup is correct, and the state is healthy." == result.message
    assert client.health.call_count == 1
    client.health.assert_called_once_with("cim")
    assert client.eval_sparql_query.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_repository_not_healthy_error(mock_agent_factory: MagicMock) -> None:
    retrieval_mock = MagicMock()
    retrieval_mock.graphdb_repository_id = "qa_dataset"
    retrieval_mock.connector_name = "qa_dataset"
    mock_agent_factory.settings.tools.retrieval_search = retrieval_mock

    client = mock_agent_factory.graphdb_client

    mock_response = MagicMock()
    mock_response.json.return_value = green_status

    client.health.side_effect = [
        mock_response,
        RepositoryNotHealthyError("Repository qa_dataset is not healthy. 500 - Not healthy")
    ]
    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert "Repository qa_dataset is not healthy. 500 - Not healthy" == result.message
    assert client.health.call_count == 2
    assert client.health.call_args_list[0].args[0] == "cim"
    assert client.health.call_args_list[1].args[0] == "qa_dataset"
    assert client.eval_sparql_query.call_count == 1
    assert client.get_autocomplete_status.call_count == 1
    assert client.get_rdf_rank_status.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_repository_not_found_error(mock_agent_factory: MagicMock) -> None:
    retrieval_mock = MagicMock()
    retrieval_mock.graphdb_repository_id = "qa_dataset"
    retrieval_mock.connector_name = "qa_dataset"
    mock_agent_factory.settings.tools.retrieval_search = retrieval_mock

    client = mock_agent_factory.graphdb_client

    mock_response = MagicMock()
    mock_response.json.return_value = green_status

    client.health.side_effect = [
        mock_response,
        RepositoryNotFoundError("Repository qa_dataset not found.")
    ]
    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert "Repository qa_dataset not found." == result.message
    assert client.health.call_count == 2
    assert client.health.call_args_list[0].args[0] == "cim"
    assert client.health.call_args_list[1].args[0] == "qa_dataset"
    assert client.eval_sparql_query.call_count == 1
    assert client.get_autocomplete_status.call_count == 1
    assert client.get_rdf_rank_status.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_red_repository(mock_agent_factory: MagicMock) -> None:
    retrieval_mock = MagicMock()
    retrieval_mock.graphdb_repository_id = "qa_dataset"
    retrieval_mock.connector_name = "qa_dataset"
    mock_agent_factory.settings.tools.retrieval_search = retrieval_mock

    client = mock_agent_factory.graphdb_client

    mock_response1 = MagicMock()
    mock_response1.json.return_value = green_status
    mock_response2 = MagicMock()
    mock_response2.json.return_value = red_status

    client.health.side_effect = [
        mock_response1,
        mock_response2
    ]
    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert "GraphDB repository \"qa_dataset\" health status is red!" == result.message
    assert client.health.call_count == 2
    assert client.health.call_args_list[0].args[0] == "cim"
    assert client.health.call_args_list[1].args[0] == "qa_dataset"
    assert client.eval_sparql_query.call_count == 1
    assert client.get_autocomplete_status.call_count == 1
    assert client.get_rdf_rank_status.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_yellow_repository(mock_agent_factory: MagicMock) -> None:
    retrieval_mock = MagicMock()
    retrieval_mock.graphdb_repository_id = "qa_dataset"
    retrieval_mock.connector_name = "qa_dataset"
    mock_agent_factory.settings.tools.retrieval_search = retrieval_mock

    client = mock_agent_factory.graphdb_client

    mock_response1 = MagicMock()
    mock_response1.json.return_value = green_status
    mock_response2 = MagicMock()
    mock_response2.json.return_value = yellow_status

    client.health.side_effect = [
        mock_response1,
        mock_response2
    ]
    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.WARNING
    assert "GraphDB repository \"qa_dataset\" health status is yellow!" == result.message
    assert client.health.call_count == 2
    assert client.health.call_args_list[0].args[0] == "cim"
    assert client.health.call_args_list[1].args[0] == "qa_dataset"
    assert client.eval_sparql_query.call_count == 1
    assert client.get_autocomplete_status.call_count == 1
    assert client.get_rdf_rank_status.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_eval_ask_query_exception(mock_agent_factory: MagicMock) -> None:
    retrieval_mock = MagicMock()
    retrieval_mock.graphdb_repository_id = "qa_dataset"
    retrieval_mock.connector_name = "qa_dataset"
    mock_agent_factory.settings.tools.retrieval_search = retrieval_mock

    client = mock_agent_factory.graphdb_client

    mock_response1 = MagicMock()
    mock_response1.json.return_value = green_status
    mock_response2 = MagicMock()
    mock_response2.json.return_value = green_status_with_connector

    client.health.side_effect = [
        mock_response1,
        mock_response2
    ]

    error_message = "Some exception"
    client.eval_sparql_query.side_effect = [
        None,
        Exception(error_message)
    ]

    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert "Some exception" == result.message
    assert client.health.call_count == 2
    assert client.health.call_args_list[0].args[0] == "cim"
    assert client.health.call_args_list[1].args[0] == "qa_dataset"
    assert client.eval_sparql_query.call_count == 2
    assert client.get_autocomplete_status.call_count == 1
    assert client.get_rdf_rank_status.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_connector_missing_same_repository(mock_agent_factory: MagicMock) -> None:
    retrieval_mock = MagicMock()
    retrieval_mock.graphdb_repository_id = "cim"
    retrieval_mock.connector_name = "qa_dataset"
    mock_agent_factory.settings.tools.retrieval_search = retrieval_mock

    client = mock_agent_factory.graphdb_client
    client.health.return_value.json.return_value = green_status
    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert "Missing connector \"qa_dataset\" for repository \"cim\"!" == result.message
    assert client.health.call_count == 1
    assert client.eval_sparql_query.call_count == 1
    assert client.get_autocomplete_status.call_count == 1
    assert client.get_rdf_rank_status.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_connector_missing(mock_agent_factory: MagicMock) -> None:
    retrieval_mock = MagicMock()
    retrieval_mock.graphdb_repository_id = "qa_dataset"
    retrieval_mock.connector_name = "qa_dataset"
    mock_agent_factory.settings.tools.retrieval_search = retrieval_mock

    client = mock_agent_factory.graphdb_client
    client.health.return_value.json.return_value = green_status
    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert "Missing connector \"qa_dataset\" for repository \"qa_dataset\"!" == result.message
    assert client.health.call_count == 2
    assert client.health.call_args_list[0].args[0] == "cim"
    assert client.health.call_args_list[1].args[0] == "qa_dataset"
    assert client.eval_sparql_query.call_count == 2
    assert client.get_autocomplete_status.call_count == 1
    assert client.get_rdf_rank_status.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_connector_missing_another_one_exists_same_repository(mock_agent_factory: MagicMock) -> None:
    retrieval_mock = MagicMock()
    retrieval_mock.graphdb_repository_id = "cim"
    retrieval_mock.connector_name = "missing_connector"
    mock_agent_factory.settings.tools.retrieval_search = retrieval_mock

    client = mock_agent_factory.graphdb_client
    client.health.return_value.json.return_value = green_status_with_connector
    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert "Missing connector \"missing_connector\" for repository \"cim\"!" == result.message
    assert client.health.call_count == 1
    assert client.eval_sparql_query.call_count == 1
    assert client.get_autocomplete_status.call_count == 1
    assert client.get_rdf_rank_status.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_connector_missing_another_one_exists(mock_agent_factory: MagicMock) -> None:
    retrieval_mock = MagicMock()
    retrieval_mock.graphdb_repository_id = "qa_dataset"
    retrieval_mock.connector_name = "missing_connector"
    mock_agent_factory.settings.tools.retrieval_search = retrieval_mock

    client = mock_agent_factory.graphdb_client
    client.health.return_value.json.return_value = green_status_with_connector
    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert "Missing connector \"missing_connector\" for repository \"qa_dataset\"!" == result.message
    assert client.health.call_count == 2
    assert client.health.call_args_list[0].args[0] == "cim"
    assert client.health.call_args_list[1].args[0] == "qa_dataset"
    assert client.eval_sparql_query.call_count == 2
    assert client.get_autocomplete_status.call_count == 1
    assert client.get_rdf_rank_status.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_connector_yellow_same_repository(mock_agent_factory: MagicMock) -> None:
    retrieval_mock = MagicMock()
    retrieval_mock.graphdb_repository_id = "cim"
    retrieval_mock.connector_name = "qa_dataset"
    mock_agent_factory.settings.tools.retrieval_search = retrieval_mock

    client = mock_agent_factory.graphdb_client
    client.health.return_value.json.return_value = green_status_with_yellow_connector
    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.WARNING
    assert f"Connector \"qa_dataset\" health status is yellow!" == result.message
    assert client.health.call_count == 1
    assert client.eval_sparql_query.call_count == 1
    assert client.get_autocomplete_status.call_count == 1
    assert client.get_rdf_rank_status.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_connector_yellow(mock_agent_factory: MagicMock) -> None:
    retrieval_mock = MagicMock()
    retrieval_mock.graphdb_repository_id = "qa_dataset"
    retrieval_mock.connector_name = "qa_dataset"
    mock_agent_factory.settings.tools.retrieval_search = retrieval_mock

    client = mock_agent_factory.graphdb_client

    mock_response1 = MagicMock()
    mock_response1.json.return_value = green_status
    mock_response2 = MagicMock()
    mock_response2.json.return_value = green_status_with_yellow_connector

    client.health.side_effect = [
        mock_response1,
        mock_response2
    ]
    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.WARNING
    assert f"Connector \"qa_dataset\" health status is yellow!" == result.message
    assert client.health.call_count == 2
    assert client.health.call_args_list[0].args[0] == "cim"
    assert client.health.call_args_list[1].args[0] == "qa_dataset"
    assert client.eval_sparql_query.call_count == 2
    assert client.get_autocomplete_status.call_count == 1
    assert client.get_rdf_rank_status.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_connector_red_same_repository(mock_agent_factory: MagicMock) -> None:
    retrieval_mock = MagicMock()
    retrieval_mock.graphdb_repository_id = "cim"
    retrieval_mock.connector_name = "qa_dataset"
    mock_agent_factory.settings.tools.retrieval_search = retrieval_mock

    client = mock_agent_factory.graphdb_client
    client.health.return_value.json.return_value = green_status_with_red_connector
    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert f"Connector \"qa_dataset\" health status is red!" == result.message
    assert client.health.call_count == 1
    assert client.eval_sparql_query.call_count == 1
    assert client.get_autocomplete_status.call_count == 1
    assert client.get_rdf_rank_status.call_count == 1


@pytest.mark.asyncio
async def test_retrieval_connector_red(mock_agent_factory: MagicMock) -> None:
    retrieval_mock = MagicMock()
    retrieval_mock.graphdb_repository_id = "qa_dataset"
    retrieval_mock.connector_name = "qa_dataset"
    mock_agent_factory.settings.tools.retrieval_search = retrieval_mock

    client = mock_agent_factory.graphdb_client

    mock_response1 = MagicMock()
    mock_response1.json.return_value = green_status
    mock_response2 = MagicMock()
    mock_response2.json.return_value = green_status_with_red_connector

    client.health.side_effect = [
        mock_response1,
        mock_response2
    ]
    client.get_autocomplete_status.return_value = GraphDBAutocompleteStatus.READY
    client.get_rdf_rank_status.return_value = GraphDBRdfRankStatus.COMPUTED

    checker = GraphDBHealthchecker(mock_agent_factory)
    result = await checker.health()

    assert result.status == HealthStatus.ERROR
    assert f"Connector \"qa_dataset\" health status is red!" == result.message
    assert client.health.call_count == 2
    assert client.health.call_args_list[0].args[0] == "cim"
    assert client.health.call_args_list[1].args[0] == "qa_dataset"
    assert client.eval_sparql_query.call_count == 2
    assert client.get_autocomplete_status.call_count == 1
    assert client.get_rdf_rank_status.call_count == 1
