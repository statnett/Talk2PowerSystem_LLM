import datetime
from unittest.mock import MagicMock

import pytest
from cognite.client.exceptions import CogniteNotFoundError
from cognite.client.testing import monkeypatch_cognite_client

from talk2powersystemllm.tools import RetrieveDataPointsTool, CogniteSession


@pytest.mark.parametrize(
    "end",
    [
        "2025-06-03", "2025-06-03T00:00:00", "2025-06-03T12:34:56Z", "2025-06-03T12:34:56+02:00", "2025-06-03T12",
        "2025-06-03T12:34", None
    ],
)
def test_correct_format_end(end: str) -> None:
    with monkeypatch_cognite_client() as c_mock:
        mock_session = MagicMock(spec=CogniteSession)
        mock_session.client.return_value = c_mock

        tool = RetrieveDataPointsTool(cognite_session=mock_session)
        tool._run(
            external_id="external_id",
            end=end,
        )

        c_mock.time_series.data.retrieve_arrays.assert_called_once()


@pytest.mark.parametrize(
    "start",
    [
        "2025-06-03", "2025-06-03T00:00:00", "2025-06-03T12:34:56Z", "2025-06-03T12:34:56+02:00", "2025-06-03T12",
        "2025-06-03T12:34", None
    ],
)
def test_correct_format_start(start: str) -> None:
    with monkeypatch_cognite_client() as c_mock:
        mock_session = MagicMock(spec=CogniteSession)
        mock_session.client.return_value = c_mock

        tool = RetrieveDataPointsTool(cognite_session=mock_session)
        tool._run(
            external_id="external_id",
            start=start
        )

        c_mock.time_series.data.retrieve_arrays.assert_called_once()


def test_external_id_doesnt_exist() -> None:
    with monkeypatch_cognite_client() as c_mock:
        c_mock.time_series.data.retrieve_arrays.side_effect = CogniteNotFoundError(
            not_found=["external_id"],
        )
        mock_session = MagicMock(spec=CogniteSession)
        mock_session.client.return_value = c_mock

        tool = RetrieveDataPointsTool(cognite_session=mock_session)
        with pytest.raises(ValueError) as exc:
            tool._run(
                external_id="external_id",
            )
        assert f"Not found: ['external_id']" == str(exc.value)

        c_mock.time_series.data.retrieve_arrays.assert_called_once_with(
            external_id="external_id",
            limit=None,
            start=None,
            end=None,
            aggregates=None,
            granularity=None,
        )


@pytest.mark.parametrize(
    "dt",
    [
        None, "", "date",
        "1w-ago", "1w-ahead", "now",
        "2025", "2025-06",
    ],
)
def test_try_to_parse_as_iso_format_invalid_iso_format(dt: str | None) -> None:
    with monkeypatch_cognite_client() as c_mock:
        mock_session = MagicMock(spec=CogniteSession)
        mock_session.client.return_value = c_mock

        tool = RetrieveDataPointsTool(cognite_session=mock_session)
        assert tool._try_to_parse_as_iso_format(dt) == dt


def test_try_to_parse_as_iso_format_valid_iso_format() -> None:
    with monkeypatch_cognite_client() as c_mock:
        mock_session = MagicMock(spec=CogniteSession)
        mock_session.client.return_value = c_mock

        tool = RetrieveDataPointsTool(cognite_session=mock_session)
        assert tool._try_to_parse_as_iso_format("2025-06-04") == datetime.datetime(
            year=2025, month=6, day=4,
            tzinfo=datetime.timezone.utc
        )
        assert tool._try_to_parse_as_iso_format("2025-06-04T14") == datetime.datetime(
            year=2025, month=6, day=4, hour=14,
            tzinfo=datetime.timezone.utc
        )
        assert tool._try_to_parse_as_iso_format("2025-06-04T14:30") == datetime.datetime(
            year=2025, month=6, day=4, hour=14, minute=30,
            tzinfo=datetime.timezone.utc
        )
        assert tool._try_to_parse_as_iso_format("2025-06-04T14:30:30") == datetime.datetime(
            year=2025, month=6, day=4, hour=14, minute=30, second=30,
            tzinfo=datetime.timezone.utc
        )
        assert tool._try_to_parse_as_iso_format("2025-06-04T14:30:30.123") == datetime.datetime(
            year=2025, month=6, day=4, hour=14, minute=30, second=30, microsecond=123000,
            tzinfo=datetime.timezone.utc
        )
        assert tool._try_to_parse_as_iso_format("2025-06-04T14:30:30Z") == datetime.datetime(
            year=2025, month=6, day=4, hour=14, minute=30, second=30,
            tzinfo=datetime.timezone.utc
        )
        assert tool._try_to_parse_as_iso_format("2025-06-04T14:30:30.123Z") == datetime.datetime(
            year=2025, month=6, day=4, hour=14, minute=30, second=30, microsecond=123000,
            tzinfo=datetime.timezone.utc,
        )
        assert tool._try_to_parse_as_iso_format("2025-06-04T14:30:30-04:00") == datetime.datetime(
            year=2025, month=6, day=4, hour=14 + 4, minute=30, second=30,
            tzinfo=datetime.timezone.utc
        )
        assert tool._try_to_parse_as_iso_format("2025-06-04T14:30:30.123-04:00") == datetime.datetime(
            year=2025, month=6, day=4, hour=14 + 4, minute=30, second=30, microsecond=123000,
            tzinfo=datetime.timezone.utc
        )
        assert tool._try_to_parse_as_iso_format("2025-06-04T14:30:30-0400") == datetime.datetime(
            year=2025, month=6, day=4, hour=14 + 4, minute=30, second=30,
            tzinfo=datetime.timezone.utc
        )
        assert tool._try_to_parse_as_iso_format("2025-06-04T14:30:30.123-0400") == datetime.datetime(
            year=2025, month=6, day=4, hour=14 + 4, minute=30, second=30, microsecond=123000,
            tzinfo=datetime.timezone.utc
        )
        assert tool._try_to_parse_as_iso_format("2025-06-04T14:30:30-04") == datetime.datetime(
            year=2025, month=6, day=4, hour=14 + 4, minute=30, second=30,
            tzinfo=datetime.timezone.utc
        )
        assert tool._try_to_parse_as_iso_format("2025-06-04T14:30:30.123-04") == datetime.datetime(
            year=2025, month=6, day=4, hour=14 + 4, minute=30, second=30, microsecond=123000,
            tzinfo=datetime.timezone.utc
        )
