Next release
============

* Bump 3rd party libraries versions

1.8.0-rc1
============

* [#255](https://github.com/statnett/Talk2PowerSystem_PM/issues/255): OBO auth flow for Cognite

1.7.0-rc1
============

* [#312](https://github.com/statnett/Talk2PowerSystem_PM/issues/312): Extend display graphics tool to support vizgraph

1.6.0-rc1
============

* [#307](https://github.com/statnett/Talk2PowerSystem_PM/issues/307): Changes in the system prompt related to the N-Shot tool usage:
  * we tell the LLM to retrieve 10 samples, not at least 10
  * we tell it to call the tool multiple times for questions consisting of multiple independent parts
  * we tell it to add the class prefixes when doing the parametrization, because the prefixes are indexed

Evaluation results with `gpt-5.2-2025-12-11`

| Split |   Micro |    Macro | (Micro) Mean Tokens | (Micro) Mean Time |
|:------|--------:|---------:|--------------------:|------------------:|
| Dev   |  0.9105 |   0.8960 |            307456.3 |             18.96 |
| Test  |  0.8333 |  0.84933 |            312005.4 |             23.17 |

* [#307](https://github.com/statnett/Talk2PowerSystem_PM/issues/307): Update `cim-subset-pretty.ttl` to the latest one

1.5.0-rc1
============

* [#302](https://github.com/statnett/Talk2PowerSystem_PM/issues/302): Improve SPARQL display in Explain (Update the version of `ttyg` from `3.0.0` to `3.1.0`)
* [#302](https://github.com/statnett/Talk2PowerSystem_PM/issues/302): Update versions of 3rd party libraries - langchain-openai, langgraph-checkpoint-redis, cognite-sdk, uvicorn, fastapi, APScheduler, cachetools

1.4.1-rc2
============

* [#301](https://github.com/statnett/Talk2PowerSystem_PM/issues/301): Revert back to relative paths for the diagrams, but add also the frontend context path as prefix

1.4.1-rc1
============

* [#301](https://github.com/statnett/Talk2PowerSystem_PM/issues/301): Return full IRI to the diagrams in the /rest/chat/conversations response body

1.4.0-rc1
============

* [#280](https://github.com/statnett/Talk2PowerSystem_PM/issues/280): Display svg diagrams
* [#280](https://github.com/statnett/Talk2PowerSystem_PM/issues/280): Show the accumulated tokens for the individual messages
* [#280](https://github.com/statnett/Talk2PowerSystem_PM/issues/280): Update the version of `ttyg` from `2.1.0` to `3.0.0`
* [#278](https://github.com/statnett/Talk2PowerSystem_PM/issues/278): Update the version of `graphrag-eval` from `5.2.0` to `5.3.1`

1.3.0-rc1
============

* [#256](https://github.com/statnett/Talk2PowerSystem_PM/issues/256): Update the queries for the ontologies and datasets information served from the `__about` endpoint
* [#251](https://github.com/statnett/Talk2PowerSystem_PM/issues/251): Change N-Shot tool configuration to default to the base GraphDB
* [#276](https://github.com/statnett/Talk2PowerSystem_PM/issues/276): Change N-Shot tool configuration SPARQL query template, so that it outputs unique SPARQL queries
* [#254](https://github.com/statnett/Talk2PowerSystem_PM/issues/254): Update the version of `ttyg` from `1.9.3` to `1.10.0`, so that the chat bot can run without admin access to GraphDB
* [#254](https://github.com/statnett/Talk2PowerSystem_PM/issues/254): Update the version of `cognite-sdk` from `7.86.0` to `7.88.0`

1.2.0-rc4
============

* [#198](https://github.com/statnett/Talk2PowerSystem_PM/issues/198): Update version of `ttyg` from `1.9.2` to `1.9.3`, so that
we can handle all possible responses for GraphDB autocomplete index status and RDF rank status

1.2.0-rc3
============

* [#198](https://github.com/statnett/Talk2PowerSystem_PM/issues/198): Introduce a new security configuration for the expected audience of the tokens

1.2.0-rc2
============

### New features

* [#236](https://github.com/statnett/Talk2PowerSystem_PM/issues/236): Update response from the `__about` endpoint to serve the required data for the components information page

### Improvements

* [#236](https://github.com/statnett/Talk2PowerSystem_PM/issues/236): Run the agent in async mode, so that other endpoints and tasks don't block

### Bug fixes

* [#252](https://github.com/statnett/Talk2PowerSystem_PM/issues/252): Fix GraphDB client execution of multiple SPARQL queries in parallel

###################

1.1.0rc1
============

### New features

* [#245](https://github.com/statnett/Talk2PowerSystem_PM/issues/245): Allow the chat bot to run with OpenAI LLM not just with Azure
* [#138](https://github.com/statnett/Talk2PowerSystem_PM/issues/138): The `now` tool now returns the date time in the user's local time zone (using a context var),
so that time series questions referencing certain point in time are relative to this time (instead of UTC), while the timestamps in Cognite are in UTC.
Also, modify the agent prompt, so that the agent is aware of that.

### Improvements

* [#138](https://github.com/statnett/Talk2PowerSystem_PM/issues/138): Update the description of the `retrieve_time_series` tool, so that the agent always fetches the external id based on the mrid from the rdf
* [#138](https://github.com/statnett/Talk2PowerSystem_PM/issues/138): Wrap the `CogniteNotFoundError` exception in `ValueError` for the `retrieve_data_points` tool, so that we propagate a better error message to the agent
* [#138](https://github.com/statnett/Talk2PowerSystem_PM/issues/138): Update ``cognite-sdk`` from ``7.83.1`` to ``7.86.0``

###################
