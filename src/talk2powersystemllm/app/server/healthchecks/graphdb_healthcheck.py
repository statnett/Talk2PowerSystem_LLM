import logging

from ttyg.graphdb import GraphDB, GraphDBRdfRankStatus

from .healthchecks import HealthChecks
from ..singleton import SingletonMeta
from ...models import HealthCheck, Severity, HealthStatus


class GraphDBHealthcheck(HealthCheck):
    severity: Severity = Severity.HIGH
    id: str = "http://talk2powersystem.no/talk2powersystem-api/graphdb-healthcheck"
    name: str = "GraphDB Health Check"
    type: str = "graphdb"
    impact: str = "Chat bot won't be able to query GraphDB or tools may not function as expected."
    troubleshooting: str = "#graphdb-health-check-status-is-not-ok"
    description: str = (
        "Checks if GraphDB repository can be queried. Also checks that the autocomplete is enabled, and "
        "RDF rank is computed.")


class GraphDBHealthchecker(metaclass=SingletonMeta):
    def __init__(
            self,
            graphdb_client: GraphDB,
    ):
        self.__graphdb_client = graphdb_client
        HealthChecks().add(self)

    async def health(self) -> GraphDBHealthcheck:
        try:
            self.__graphdb_client.eval_sparql_query("ASK { ?s ?p ?o }", validation=False)
            if not self.__graphdb_client.autocomplete_is_enabled():
                warning_message = "GraphDB Autocomplete index is not enabled. It should be enabled."
                logging.warning(warning_message)
                return GraphDBHealthcheck(status=HealthStatus.WARNING, message=warning_message)

            rdf_rank_status = self.__graphdb_client.get_rdf_rank_status()
            if rdf_rank_status != GraphDBRdfRankStatus.COMPUTED:
                warning_message = (f"The RDF Rank status of the repository is \"{rdf_rank_status.name}\". "
                                   f"It should be \"COMPUTED\".")
                logging.warning(warning_message)
                return GraphDBHealthcheck(status=HealthStatus.WARNING, message=warning_message)
            return GraphDBHealthcheck(
                status=HealthStatus.OK, message="GraphDB repository can be queried and it's configured correctly."
            )
        except Exception as error:
            logging.error("Exception while querying GraphDB", exc_info=error)
            return GraphDBHealthcheck(status=HealthStatus.ERROR, message=str(error))
