import logging

from rdflib.contrib.graphdb.exceptions import (
    RepositoryNotFoundError,
    RepositoryNotHealthyError,
)
from ttyg.graphdb import (
    GraphDBRdfRankStatus,
    GraphDBAutocompleteStatus,
)

from talk2powersystemllm.agent import Talk2PowerSystemAgentFactory
from talk2powersystemllm.app.models import HealthCheck, Severity, HealthStatus
from talk2powersystemllm.app.server.services.healthchecks.healthchecks import HealthProvider

logger = logging.getLogger(__name__)


class GraphDBHealthcheck(HealthCheck):
    severity: Severity = Severity.HIGH
    id: str = "http://talk2powersystem.no/talk2powersystem-api/graphdb-healthcheck"
    name: str = "GraphDB Health Check"
    type: str = "graphdb"
    impact: str = "Chat bot won't be able to query GraphDB or tools may not function as expected."
    troubleshooting: str = "#graphdb-health-check-status-is-not-ok"
    description: str = (
        "Checks that the GraphDB repository can be queried and is healthy. "
        "Checks that the status of the autocomplete index is READY, and the RDF rank status is COMPUTED. "
        "In addition, if the n-shot tool is available, checks that the n-shot tool GraphDB repository "
        "can be queried and is healthy, and that the ChatGPT Retrieval Plugin connector exists and its status is "
        "healthy."
    )


class GraphDBHealthchecker(HealthProvider):
    def __init__(self, agent_factory: Talk2PowerSystemAgentFactory):
        self.__graphdb_client = agent_factory.graphdb_client
        self.__repository_id = agent_factory.graphdb_repository_id

        self.__retrieval_repository_id = None
        self.__retrieval_connector_name = None
        if agent_factory.sample_sparql_queries_enabled:
            retrieval_search_settings = agent_factory.sample_sparql_queries_settings
            self.__retrieval_repository_id = retrieval_search_settings.graphdb_repository_id
            self.__retrieval_connector_name = retrieval_search_settings.connector_name

    async def health(self) -> GraphDBHealthcheck:
        try:
            status, msg, health_response = self.__check_repository_health(self.__repository_id)
            if status != HealthStatus.OK:
                return GraphDBHealthcheck(status=status, message=msg)

            status, msg = self.__check_autocomplete_status()
            if status != HealthStatus.OK:
                return GraphDBHealthcheck(status=status, message=msg)

            status, msg = self.__check_rdf_rank_status()
            if status != HealthStatus.OK:
                return GraphDBHealthcheck(status=status, message=msg)

            if self.__retrieval_repository_id:
                if self.__retrieval_repository_id != self.__repository_id:
                    status, msg, retrieval_health_response = self.__check_repository_health(
                        self.__retrieval_repository_id
                    )
                    if status != HealthStatus.OK:
                        return GraphDBHealthcheck(status=status, message=msg)
                else:
                    retrieval_health_response = health_response

                status, msg = self.__check_connector_health(retrieval_health_response)
                if status != HealthStatus.OK:
                    return GraphDBHealthcheck(status=status, message=msg)

            return GraphDBHealthcheck(
                status=HealthStatus.OK,
                message="GraphDB can be queried, the setup is correct, and the state is healthy."
            )

        except Exception as error:
            logger.exception("Exception raised in GraphDB health check")
            return GraphDBHealthcheck(status=HealthStatus.ERROR, message=str(error))

    def __check_repository_health(self, repository_id: str) -> tuple[HealthStatus, str, dict | None]:
        try:
            health_response = self.__graphdb_client.health(repository_id).json()
            if health_response["status"] in ("yellow", "red"):
                status = HealthStatus.WARNING if health_response["status"] == "yellow" else HealthStatus.ERROR
                msg = f"GraphDB repository \"{repository_id}\" health status is {health_response["status"]}!"
                self.__log(status, f"GraphDB health response for repository \"{repository_id}\" was {health_response}")
                self.__log(status, msg)
                return status, msg, health_response

            self.__graphdb_client.eval_sparql_query(repository_id, "ASK { ?s ?p ?o }", validation=False)
            return HealthStatus.OK, "", health_response

        except (RepositoryNotFoundError, RepositoryNotHealthyError) as e:
            self.__log(HealthStatus.ERROR, str(e))
            return HealthStatus.ERROR, str(e), None

    @staticmethod
    def __log(status: HealthStatus, message: str) -> None:
        if status == HealthStatus.ERROR:
            logger.error(message)
        else:
            logger.warning(message)

    def __check_autocomplete_status(self) -> tuple[HealthStatus, str]:
        autocomplete_status = self.__graphdb_client.get_autocomplete_status(self.__repository_id)
        if autocomplete_status != GraphDBAutocompleteStatus.READY:
            msg = (f"The Autocomplete index status of the repository is \"{autocomplete_status.name}\". "
                   "It should be \"READY\".")
            self.__log(HealthStatus.WARNING, msg)
            return HealthStatus.WARNING, msg
        return HealthStatus.OK, ""

    def __check_rdf_rank_status(self) -> tuple[HealthStatus, str]:
        rdf_rank_status = self.__graphdb_client.get_rdf_rank_status(self.__repository_id)
        if rdf_rank_status != GraphDBRdfRankStatus.COMPUTED:
            msg = (f"The RDF Rank status of the repository is \"{rdf_rank_status.name}\". "
                   "It should be \"COMPUTED\".")
            self.__log(HealthStatus.WARNING, msg)
            return HealthStatus.WARNING, msg
        return HealthStatus.OK, ""

    def __check_connector_health(self, health_response: dict) -> tuple[HealthStatus, str]:
        plugins = next(
            (
                component
                for component in health_response.get("components", [])
                if component.get("name") == "plugins"
            ),
            {}
        )
        chatgpt_retrieval_plugin = next(
            (
                component
                for component in plugins.get("components", [])
                if component.get("name") == "chatgpt-retrieval-connector"
            ),
            {}
        )
        connector = next(
            (
                component
                for component in chatgpt_retrieval_plugin.get("components", [])
                if component.get("name") == self.__retrieval_connector_name
            ),
            None
        )

        if not connector:
            msg = (f"Missing connector \"{self.__retrieval_connector_name}\" for repository "
                   f"\"{self.__retrieval_repository_id}\"!")
            self.__log(HealthStatus.ERROR, msg)
            return HealthStatus.ERROR, msg

        if connector["status"] in ("yellow", "red"):
            status = HealthStatus.WARNING if connector["status"] == "yellow" else HealthStatus.ERROR
            msg = f"Connector \"{self.__retrieval_connector_name}\" health status is {connector["status"]}!"
            self.__log(status, msg)
            return status, msg

        return HealthStatus.OK, ""
