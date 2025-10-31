Next release
============

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
