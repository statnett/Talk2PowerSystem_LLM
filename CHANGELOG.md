v2.4.1
============

* [#369](https://github.com/statnett/Talk2PowerSystem_PM/issues/369):
  Disable parallel tools calls to prevent the agent from hitting 
  `Param.postParse2() missing 1 required positional argument: 'tokenList'`

v2.4.0
============

* [#282](https://github.com/statnett/Talk2PowerSystem_PM/issues/282):
  - Fix Q&A dataset issues with encoding, duplicate template ids, 
    invalid values for timeseries aggregates, and empty reference steps groups.
  - Update `ttyg` to `4.2.1`, `graphrag-eval` to `6.1.0`, `cognite-sdk` to 
    `8.2.0`.
  - Rename `retrieve timeseries` tool argument `rndp_mrid` to `mrid` for the 
    sake of the evaluation.

v2.4.0-rc1
============

* [#363](https://github.com/statnett/Talk2PowerSystem_PM/issues/363):
  - Change App description and replace all occurrences of 'chat bot' with 
  'chatbot'.
  - Update `langchain-openai` to `1.2.1`, `fastapi` to `0.136.1`.

v2.3.0-rc1
============

* [#363](https://github.com/statnett/Talk2PowerSystem_PM/issues/363):
  - Implement access to Cognite with a service account.
  - Environment variable `COGNITE_CLIENT_SECRET`
  (`tools.cognite.client_secret` in the agent config) used for OBO 
  authentication to Cognite is renamed to `COGNITE_OBO_CLIENT_SECRET`
  (`tools.cognite.obo_client_secret` in the agent config).
  - Bring back Cognite health check for deployments with service 
    account or with a token from a file.
    For deployments with OBO authentication, the health check is disabled.
  - Update `langchain-openai` to `1.2.0`,
    `langgraph-checkpoint-redis` to `0.4.1`, `cognite-sdk` to `8.1.0`, 
    `pydantic-settings` to `2.14.0`, `uvicorn` to `0.46.0`,
    `fastapi` to `0.136.0`, `msal` to `1.36.0`, `cachetools` to `7.0.6`, 
    `importlib_resources` to `7.1.0`, update some other transitive 
    dependencies to their latest versions to address the security 
    vulnerabilities.
* [#362](https://github.com/statnett/Talk2PowerSystem_PM/issues/362):
  Use `RNDP_mrid` metadata instead of `mrid` for time series.
  Add hard filter for timeseries having `RNDP_mrid` metadata.

v2.2.0-rc1
============

* [#358](https://github.com/statnett/Talk2PowerSystem_PM/issues/358):
  Update the context diagram in the trouble.md document and keep a copy of it 
  in the source code.
* [#358](https://github.com/statnett/Talk2PowerSystem_PM/issues/358):
  Update `cognite-sdk` to `8.0.5`, `uvicorn` to `0.44.0`,
  `fastapi` to `0.135.3`, update some other transitive dependencies to their 
  latest versions to address the security vulnerabilities.
* [#358](https://github.com/statnett/Talk2PowerSystem_PM/issues/358):
  Support for OpenAI/Azure OpenAI Responses API.
* [#358](https://github.com/statnett/Talk2PowerSystem_PM/issues/358):
  Expose reasoning effort as configuration.

v2.1.0-rc1
============

* [#285](https://github.com/statnett/Talk2PowerSystem_PM/issues/285):
  - Update the diagrams to the regenerated ones including Telemark120.
  - Update the diagrams interactions instructions in the prompt to expect
  multiple IRIs, not just one or two.

v2.0.0
============

* Official release of `v2.0.0-rc3` as `v2.0.0`

v2.0.0-rc3
============

* [#357](https://github.com/statnett/Talk2PowerSystem_PM/issues/357):
  - Update JSON schemas for the requests and the responses from the REST API.
  - Update some 3rd party libraries to their latest versions.

v2.0.0-rc2
============

* [#359](https://github.com/statnett/Talk2PowerSystem_PM/issues/359):
  Encode the query parameters of the GraphDB Visual graph link and of the 
  PowSyBl diagrams.

v2.0.0-rc1
============

* [#349](https://github.com/statnett/Talk2PowerSystem_PM/issues/349):
  - Update `ttyg` to `4.2.0`, which uses the GraphDB client from rdflib 
  to solve the known issue that the SPARQL queries are executed 
  against GraphDB without using a connection pool.
  As a result the configuration `graphdb.sparql_timeout` is no longer available.
  - The N-Shot Tool (Retrieval Tool) now uses the same GraphDB client
  as the other tools, and not a separate one like it used to be.
  The GraphDB repository id for it is passed as `graphdb_repository_id` 
  instead of `graphdb.repository_id`.
  - Refactor the code used to evaluate open source LLMs:
    - Delete from the source code the script `run_evaluation_hf.py`.
    `run_evaluation.py` must be used instead.
    - Delete from the source code `agent_hf.py` and add new `llm.type` 
    option, which is `hugging_face`.
  - Update some 3rd party libraries to their latest versions.
* [#294](https://github.com/statnett/Talk2PowerSystem_PM/issues/294):
  Update trouble.md example responses to include `embedded=true` in the GraphDB
  VizGraph link.
* [#292](https://github.com/statnett/Talk2PowerSystem_PM/issues/292):
  Update the response from the `explain` endpoint to include 
  the GraphDB repository id for the GraphDB tools, so that the UI can build
  the url to the GraphDB Workbench with the preloaded query correctly.
* [#300](https://github.com/statnett/Talk2PowerSystem_PM/issues/300):
  Update the response from the `explain` endpoint to include additional fields 
  "advanced" and "hideArgs" to indicate the UI that a tool call or its 
  arguments by default shouldn't be displayed.
* [#315](https://github.com/statnett/Talk2PowerSystem_PM/issues/315):
  - Implement additional checks for the GraphDB health:
    - Call `/repositories/{repositoryId}/health` endpoint for the main GraphDB
    repository to catch long-running queries.
    - Check the n-shot tool repository is present and healthy, if the n-shot 
    tool
    is available.
    - Check the n-shot tool connector is present and healthy, if the n-shot tool
    is available.
  - Implement LLM health check, which checks if any LLM errors were hit in 
  the last 60 seconds. The data is persisted in Redis.
  - Code refactoring including, but not limited to:
    - split the large app server file
    - use of dependencies instead of globals
    - improve logging by using individual loggers and not the root logger
    - code re-formatting
    - usage of absolute imports instead of relative ones
* [#356](https://github.com/statnett/Talk2PowerSystem_PM/issues/356):
  Run acceptance tests with GraphDB 11.3.1

v1.9.0-rc2
============

* [#294](https://github.com/statnett/Talk2PowerSystem_PM/issues/294):
  - Change "iframe" type to "vizGraph"
  - Add query param "embedded=true" to the GraphDB VizGraph link

v1.9.0-rc1
============

* Bump 3rd party libraries versions
* [#294](https://github.com/statnett/Talk2PowerSystem_PM/issues/294):
  - Updated the response for the svg diagrams, so that we can implement the
  interactions with the diagrams
  - Updated path to the PowSyBl diagrams packaged to the Docker image
  - Updated `ttyg` to `3.2.0` to allow execution of asymmetric DESCRIBE

v1.8.0-rc1
============

* [#255](https://github.com/statnett/Talk2PowerSystem_PM/issues/255):
  OBO auth flow for Cognite

v1.7.0-rc1
============

* [#312](https://github.com/statnett/Talk2PowerSystem_PM/issues/312):
  Extend display graphics tool to support vizgraph

v1.6.0-rc1
============

* [#307](https://github.com/statnett/Talk2PowerSystem_PM/issues/307):
  - Update `cim-subset-pretty.ttl` to the latest one
  - Changes in the system prompt related to the N-Shot tool usage:
    - we tell the LLM to retrieve 10 samples, not at least 10
    - we tell it to call the tool multiple times for questions consisting of 
    multiple independent parts
    - we tell it to add the class prefixes when doing the parametrization, 
    because the prefixes are indexed

Evaluation results with `gpt-5.2-2025-12-11`

| Split |   Micro |    Macro | (Micro) Mean Tokens | (Micro) Mean Time |
|:------|--------:|---------:|--------------------:|------------------:|
| Dev   |  0.9105 |   0.8960 |            307456.3 |             18.96 |
| Test  |  0.8333 |  0.84933 |            312005.4 |             23.17 |

1.5.0-rc1
============

* [#302](https://github.com/statnett/Talk2PowerSystem_PM/issues/302):
  - Improve SPARQL display in Explain
  (Update the version of `ttyg` from `3.0.0` to `3.1.0`)
  - Update versions of 3rd party libraries - langchain-openai, 
  langgraph-checkpoint-redis, cognite-sdk, uvicorn, fastapi, APScheduler,
  cachetools

v1.4.1-rc2
============

* [#301](https://github.com/statnett/Talk2PowerSystem_PM/issues/301):
  Revert back to relative paths for the diagrams, but add also the frontend 
  context path as prefix

v1.4.1-rc1
============

* [#301](https://github.com/statnett/Talk2PowerSystem_PM/issues/301):
  Return full IRI to the diagrams in the /rest/chat/conversations response body

v1.4.0-rc1
============

* [#278](https://github.com/statnett/Talk2PowerSystem_PM/issues/278):
  Update the version of `graphrag-eval` from `5.2.0` to `5.3.1`
* Update some 3rd party libraries to their latest versions including an update 
of `langchain` to version `1.1.0`
* [#280](https://github.com/statnett/Talk2PowerSystem_PM/issues/280):
  - Display svg diagrams
  - Show the accumulated tokens for the individual messages
  - Update the version of `ttyg` to `3.0.0`

v1.3.0-rc1
============

* [#256](https://github.com/statnett/Talk2PowerSystem_PM/issues/256):
  - Update the queries for the ontologies and datasets information served from
  the `__about` endpoint
  - Update the __about SPARQL queries in the trouble doc
* [#251](https://github.com/statnett/Talk2PowerSystem_PM/issues/251):
  Change N-Shot tool configuration to default to the base GraphDB
* [#276](https://github.com/statnett/Talk2PowerSystem_PM/issues/276):
  - Change N-Shot tool configuration SPARQL query template, so that it outputs 
  unique SPARQL queries
  - Update cim-subset-pretty to the latest one
* [#254](https://github.com/statnett/Talk2PowerSystem_PM/issues/254):
  - Update the version of `ttyg` from `1.9.3` to `1.10.0`, so that the chat bot 
  can run without admin access to GraphDB
  - Update the version of `cognite-sdk` from `7.86.0` to `7.88.0`
* [#240](https://github.com/statnett/Talk2PowerSystem_PM/issues/240):
  Update the version of graphrag-eval to 5.2.0, which compares the SPARQL
  results as set, not as list
* [#250](https://github.com/statnett/Talk2PowerSystem_PM/issues/250):
  Change N-Shot tool configuration SPARQL query template

v1.2.0-rc4
============

* [#198](https://github.com/statnett/Talk2PowerSystem_PM/issues/198):
  Update version of `ttyg` from `1.9.2` to `1.9.3`, so that
  we can handle all possible responses for GraphDB autocomplete index status and
  RDF rank status

v1.2.0-rc3
============

* [#198](https://github.com/statnett/Talk2PowerSystem_PM/issues/198):
  Introduce a new security configuration for the expected audience of the tokens

v1.2.0-rc2
============

* [#198](https://github.com/statnett/Talk2PowerSystem_PM/issues/198):
  Fix git branch name in the manifest
* [#252](https://github.com/statnett/Talk2PowerSystem_PM/issues/252):
  Fix GraphDB client execution of multiple SPARQL queries in parallel

v1.2.0-rc1
============

* [#236](https://github.com/statnett/Talk2PowerSystem_PM/issues/236):
  - Update response from the `__about` endpoint to serve the required data for 
  the components information page
  - Run the agent in async mode, so that other endpoints and tasks don't block
* [#196](https://github.com/statnett/Talk2PowerSystem_PM/issues/196): 
  - Fix the version in the pyproject.toml, so that it's a valid semver version
  - Update versioning section with the release process

###################

1.1.0rc1
============

* [#217](https://github.com/statnett/Talk2PowerSystem_PM/issues/217):
  Update the evaluation to use the latest version of the library
* [#142](https://github.com/statnett/Talk2PowerSystem_PM/issues/142):
  Benchmark GraphDB TTYG
* [#138](https://github.com/statnett/Talk2PowerSystem_PM/issues/138):
  - The `now` tool now returns the date time in the user's local time zone
    (using a context var),
    so that time series questions referencing certain point in time are
    relative to this time (instead of UTC), while the timestamps in Cognite are
    in UTC.
    Also, modify the agent prompt, so that the agent is aware of that.
  - Update the description of the `retrieve_time_series` tool, so that the
    agent always fetches the external id based on the mrid from the rdf
  - Wrap the `CogniteNotFoundError` exception in `ValueError` for the
    `retrieve_data_points` tool, so that we propagate a better error message
     to the agent
  - Update ``cognite-sdk`` from ``7.83.1`` to ``7.86.0``
* [#245](https://github.com/statnett/Talk2PowerSystem_PM/issues/245):
  Allow the chatbot to run with OpenAI LLM not just with Azure

###################

v1.0.0-TR-2
============

* [#122](https://github.com/statnett/Talk2PowerSystem_PM/issues/122):
 Change prompt so that we can handle literal comparison
* [#184](https://github.com/statnett/Talk2PowerSystem_PM/issues/184):
  Update Jupyter Notebook instructions after the RNDP upgrade
* [#176](https://github.com/statnett/Talk2PowerSystem_PM/issues/176):
  - The overall gtg is OK if there is a high severity health check with status
    warning
  - Update versions of some 3rd party libraries
* [#185](https://github.com/statnett/Talk2PowerSystem_PM/issues/185):
  Chatbot authentication
* [#198](https://github.com/statnett/Talk2PowerSystem_PM/issues/198):
  Access Cognite from RNDP
* [#210](https://github.com/statnett/Talk2PowerSystem_PM/issues/210):
  Use multistage build, use python:3.12.11-slim as base imagе
* [#198](https://github.com/statnett/Talk2PowerSystem_PM/issues/198):
 Fix Cognite access from the app, fix tests

v1.0.0-TR-1
============

* [#26](https://github.com/statnett/Talk2PowerSystem_PM/issues/26):
  Talk2PowerSystem notebook
* [#71](https://github.com/statnett/Talk2PowerSystem_PM/issues/71):
  Dump enumerations and string enumerations as part of the ontology schema
* Comply with the latest data changes
* [#68](https://github.com/statnett/Talk2PowerSystem_PM/issues/68):
  Add hint for mridSignificantPart
* [#113](https://github.com/statnett/Talk2PowerSystem_PM/issues/113):
  Develop Cognite Query Tool
* [#96](https://github.com/statnett/Talk2PowerSystem_PM/issues/96):
  Chatbot now uses cim-subset-pretty
* [#110](https://github.com/statnett/Talk2PowerSystem_PM/issues/110):
  Sync evaluation script with the GSC changes
* [#66](https://github.com/statnett/Talk2PowerSystem_PM/issues/66):
  Update evaluation version including some bug fixes, split the corpus into
  train, dev and test
* [#116](https://github.com/statnett/Talk2PowerSystem_PM/issues/116):
  Chat bot bow uses cims:pragmatics
* Configure the chatbot to run on the RNDP environment
* [#127](https://github.com/statnett/Talk2PowerSystem_PM/issues/127):
  Chat Bot Backend App
* [#26](https://github.com/statnett/Talk2PowerSystem_PM/issues/26):
  Update Jupyter Notebook RNDP documentation
* [#134](https://github.com/statnett/Talk2PowerSystem_PM/issues/134):
  Redis as memory storage for the chatbot, GraphDB timeouts config
