Next release
============

### New features

* [#138](https://github.com/statnett/Talk2PowerSystem_PM/issues/138): The `now` tool now returns the date time in the user's local time zone (using a context var),
so that time series questions referencing certain point in time are relative to this time (instead of UTC), while the timestamps in Cognite are in UTC.
Also, modify the agent prompt, so that the agent is aware of that.

### Improvements

* [#138](https://github.com/statnett/Talk2PowerSystem_PM/issues/138): Update the description of the `retrieve_time_series` tool, so that the agent always fetches the external id based on the mrid from the rdf
* [#138](https://github.com/statnett/Talk2PowerSystem_PM/issues/138): Wrap the `CogniteNotFoundError` exception in `ValueError` for the `retrieve_data_points` tool, so that we propagate a better error message to the agent
* [#138](https://github.com/statnett/Talk2PowerSystem_PM/issues/138): Update ``cognite-sdk`` from ``7.83.1`` to ``7.86.0``

###################
