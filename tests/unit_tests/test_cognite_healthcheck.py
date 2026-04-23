from unittest.mock import MagicMock

import pytest
from cognite.client.data_classes import TimeSeriesList
from cognite.client.testing import monkeypatch_cognite_client

from talk2powersystemllm.app.models import HealthStatus
from talk2powersystemllm.app.server.services import CogniteHealthchecker
from talk2powersystemllm.tools import CogniteSession


@pytest.mark.asyncio
async def test_success() -> None:
    with monkeypatch_cognite_client() as c_mock:
        mock_session = MagicMock(spec=CogniteSession)
        mock_session.client.return_value = c_mock

        c_mock.time_series.list.return_value = TimeSeriesList._load(
            [
                {
                    "id": 123,
                    "createdTime": "2020-05-05 20:11:02.889+00:00",
                    "lastUpdatedTime": "2026-03-20 12:52:36.275+00:00",
                    "isStep": False,
                    "isString": False,
                }
            ]
        )

        checker = CogniteHealthchecker(mock_session)
        result = await checker.health()

        assert result.status == HealthStatus.OK
        assert result.message == "Cognite can be queried."

        c_mock.time_series.list.assert_called_once()


@pytest.mark.asyncio
async def test_error() -> None:
    with monkeypatch_cognite_client() as c_mock:
        mock_session = MagicMock(spec=CogniteSession)
        mock_session.client.return_value = c_mock

        c_mock.time_series.list.side_effect = Exception()

        checker = CogniteHealthchecker(mock_session)
        result = await checker.health()

        assert result.status == HealthStatus.ERROR
        assert result.message == "Cognite error "

        c_mock.time_series.list.assert_called_once()
