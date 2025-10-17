import logging

from ttyg.graphdb import (
    GraphDB,
    GraphDBRdfRankStatus,
    GraphDBAutocompleteStatus,
)

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
        "Checks if GraphDB repository can be queried. Also checks that the status of the autocomplete index is READY, "
        "and the RDF rank status is COMPUTED.")


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
            autocomplete_status = self.__graphdb_client.get_autocomplete_status()
            if autocomplete_status != GraphDBAutocompleteStatus.READY:
                warning_message = (f"The Autocomplete index status of the repository is \"{autocomplete_status.name}\". "
                                   f"It should be \"READY\".")
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
