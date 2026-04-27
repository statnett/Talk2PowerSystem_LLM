import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import SecretStr

from talk2powersystemllm.agent import CogniteSettings, LLMSettings, LLMType


def test_llm_settings_openai_success():
    settings = LLMSettings(
        type=LLMType.openai,
        model="gpt-5.4",
        reasoning_effort="high",
        api_key=SecretStr("secret-key"),
    )
    assert settings.type == LLMType.openai
    assert settings.model == "gpt-5.4"
    assert settings.azure_endpoint is None
    assert settings.api_version is None
    assert settings.hugging_face_endpoint is None
    assert settings.temperature is None
    assert settings.use_responses_api is None
    assert settings.reasoning_effort == "high"
    assert settings.seed is None
    assert settings.timeout == 120
    assert settings.api_key.get_secret_value() == "secret-key"


def test_llm_settings_default_azure_success():
    settings = LLMSettings(
        model="gpt-5.4",
        azure_endpoint="https://example.openai.azure.com",
        api_version="2024-02-15-preview",
        reasoning_effort="high",
        api_key=SecretStr("secret-key"),
    )
    assert settings.type == LLMType.azure_openai
    assert settings.model == "gpt-5.4"
    assert settings.azure_endpoint == "https://example.openai.azure.com"
    assert settings.api_version == "2024-02-15-preview"
    assert settings.hugging_face_endpoint is None
    assert settings.temperature is None
    assert settings.use_responses_api is None
    assert settings.reasoning_effort == "high"
    assert settings.seed is None
    assert settings.timeout == 120
    assert settings.api_key.get_secret_value() == "secret-key"


def test_llm_settings_azure_missing_endpoint_and_version():
    with pytest.raises(ValueError, match="azure_endpoint is required!"):
        LLMSettings(
            model="gpt-5.4",
            api_key=SecretStr("secret-key"),
        )


def test_llm_settings_azure_missing_endpoint():
    with pytest.raises(ValueError, match="azure_endpoint is required!"):
        LLMSettings(
            model="gpt-5.4",
            api_version="2024-02-15-preview",
            api_key=SecretStr("secret-key"),
        )


def test_llm_settings_azure_missing_version():
    with pytest.raises(ValueError, match="api_version is required!"):
        LLMSettings(
            model="gpt-5.4",
            azure_endpoint="https://example.openai.azure.com",
            api_key=SecretStr("secret-key"),
        )


def test_llm_settings_hugging_face_success():
    settings = LLMSettings(
        type=LLMType.hugging_face,
        model="llama-3",
        hugging_face_endpoint="https://api-inference.huggingface.co/models/llama",
        temperature=1,
        seed=42,
        timeout=60,
        api_key=SecretStr("secret-key"),
    )
    assert settings.type == LLMType.hugging_face
    assert settings.model == "llama-3"
    assert settings.azure_endpoint is None
    assert settings.api_version is None
    assert (
        settings.hugging_face_endpoint
        == "https://api-inference.huggingface.co/models/llama"
    )
    assert settings.temperature == 1
    assert settings.use_responses_api is None
    assert settings.reasoning_effort is None
    assert settings.seed == 42
    assert settings.timeout == 60
    assert settings.api_key.get_secret_value() == "secret-key"


def test_llm_settings_hugging_endpoint_missing():
    with pytest.raises(ValueError, match="hugging_face_endpoint is required!"):
        LLMSettings(
            type=LLMType.hugging_face,
            model="llama-3",
            api_key=SecretStr("secret-key"),
        )


def test_llm_settings_responses_api_and_seed_conflict():
    with pytest.raises(
        ValueError,
        match="`seed` is not supported by the Responses API. "
        "Please, remove it, or use the Completions API.",
    ):
        LLMSettings(
            model="gpt-5.4",
            azure_endpoint="https://example.openai.azure.com",
            api_version="2024-02-15-preview",
            use_responses_api=True,
            seed=0,
            api_key=SecretStr("secret-key"),
        )

    with pytest.raises(
        ValueError,
        match="`seed` is not supported by the Responses API. "
        "Please, remove it, or use the Completions API.",
    ):
        LLMSettings(
            model="gpt-5.4",
            azure_endpoint="https://example.openai.azure.com",
            api_version="2024-02-15-preview",
            use_responses_api=True,
            seed=42,
            api_key=SecretStr("secret-key"),
        )

    with pytest.raises(
        ValueError,
        match="`seed` is not supported by the Responses API. "
        "Please, remove it, or use the Completions API.",
    ):
        LLMSettings(
            type=LLMType.openai,
            model="gpt-5.4",
            use_responses_api=True,
            seed=0,
            api_key=SecretStr("secret-key"),
        )

    with pytest.raises(
        ValueError,
        match="`seed` is not supported by the Responses API. "
        "Please, remove it, or use the Completions API.",
    ):
        LLMSettings(
            type=LLMType.openai,
            model="gpt-5.4",
            use_responses_api=True,
            seed=42,
            api_key=SecretStr("secret-key"),
        )


def test_llm_settings_responses_api_without_seed_success():
    settings = LLMSettings(
        model="gpt-5.4",
        azure_endpoint="https://example.openai.azure.com",
        api_version="2024-02-15-preview",
        use_responses_api=True,
        api_key=SecretStr("secret-key"),
    )
    assert settings.type == LLMType.azure_openai
    assert settings.model == "gpt-5.4"
    assert settings.azure_endpoint == "https://example.openai.azure.com"
    assert settings.api_version == "2024-02-15-preview"
    assert settings.hugging_face_endpoint is None
    assert settings.temperature is None
    assert settings.use_responses_api
    assert settings.reasoning_effort is None
    assert settings.seed is None
    assert settings.timeout == 120
    assert settings.api_key.get_secret_value() == "secret-key"

    settings = LLMSettings(
        type=LLMType.openai,
        model="gpt-5.4",
        use_responses_api=True,
        api_key=SecretStr("secret-key"),
    )
    assert settings.type == LLMType.openai
    assert settings.model == "gpt-5.4"
    assert settings.azure_endpoint is None
    assert settings.api_version is None
    assert settings.hugging_face_endpoint is None
    assert settings.temperature is None
    assert settings.use_responses_api
    assert settings.reasoning_effort is None
    assert settings.seed is None
    assert settings.timeout == 120
    assert settings.api_key.get_secret_value() == "secret-key"


def test_llm_settings_env_prefix_loading():
    with patch.dict(
        os.environ,
        {
            "LLM_API_KEY": "secret-key",
        },
    ):
        settings = LLMSettings(
            model="gpt-5.4",
            azure_endpoint="https://example.openai.azure.com",
            api_version="2024-02-15-preview",
        )
        assert settings.type == LLMType.azure_openai
        assert settings.model == "gpt-5.4"
        assert settings.azure_endpoint == "https://example.openai.azure.com"
        assert settings.api_version == "2024-02-15-preview"
        assert settings.hugging_face_endpoint is None
        assert settings.temperature is None
        assert settings.use_responses_api is None
        assert settings.reasoning_effort is None
        assert settings.seed is None
        assert settings.timeout == 120
        assert settings.api_key.get_secret_value() == "secret-key"


def test_llm_settings_temperature_range_validation():
    with pytest.raises(ValueError):
        LLMSettings(
            model="gpt-5.4",
            azure_endpoint="https://example.openai.azure.com",
            api_version="2024-02-15-preview",
            temperature=2.1,
            use_responses_api=True,
            api_key=SecretStr("secret-key"),
        )

    with pytest.raises(ValueError):
        LLMSettings(
            model="gpt-5.4",
            azure_endpoint="https://example.openai.azure.com",
            api_version="2024-02-15-preview",
            temperature=-0.1,
            use_responses_api=True,
            api_key=SecretStr("secret-key"),
        )


def test_llm_settings_timeout_range_validation():
    with pytest.raises(ValueError):
        LLMSettings(
            model="gpt-5.4",
            azure_endpoint="https://example.openai.azure.com",
            api_version="2024-02-15-preview",
            timeout=0,
            use_responses_api=True,
            api_key=SecretStr("secret-key"),
        )

    with pytest.raises(ValueError):
        LLMSettings(
            model="gpt-5.4",
            azure_endpoint="https://example.openai.azure.com",
            api_version="2024-02-15-preview",
            timeout=-1,
            use_responses_api=True,
            api_key=SecretStr("secret-key"),
        )


def test_cognite_settings_missing_or_additional_properties():
    with pytest.raises(
        ValueError,
        match="Pass exactly one of 'interactive_client_id', 'client_id', 'token_file_path' or "
        "'obo_client_secret'!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
        )

    with pytest.raises(
        ValueError,
        match="Pass exactly one of 'interactive_client_id', 'client_id', 'token_file_path' or "
        "'obo_client_secret'!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
            interactive_client_id="123",
            client_id="123",
        )

    with pytest.raises(
        ValueError,
        match="Pass exactly one of 'interactive_client_id', 'client_id', 'token_file_path' or "
        "'obo_client_secret'!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
            interactive_client_id="123",
            token_file_path=Path(),
        )

    with pytest.raises(
        ValueError,
        match="Pass exactly one of 'interactive_client_id', 'client_id', 'token_file_path' or "
        "'obo_client_secret'!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
            interactive_client_id="123",
            obo_client_secret="secret-key",
        )

    with pytest.raises(
        ValueError,
        match="Pass exactly one of 'interactive_client_id', 'client_id', 'token_file_path' or "
        "'obo_client_secret'!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
            client_id="123",
            token_file_path=Path(),
        )

    with pytest.raises(
        ValueError,
        match="Pass exactly one of 'interactive_client_id', 'client_id', 'token_file_path' or "
        "'obo_client_secret'!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
            client_id="123",
            obo_client_secret="secret-key",
        )

    with pytest.raises(
        ValueError,
        match="Pass exactly one of 'interactive_client_id', 'client_id', 'token_file_path' or "
        "'obo_client_secret'!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
            token_file_path=Path(),
            obo_client_secret="secret-key",
        )

    with pytest.raises(
        ValueError,
        match="Pass exactly one of 'interactive_client_id', 'client_id', 'token_file_path' or "
        "'obo_client_secret'!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
            interactive_client_id="123",
            client_id="123",
            token_file_path=Path(),
        )

    with pytest.raises(
        ValueError,
        match="Pass exactly one of 'interactive_client_id', 'client_id', 'token_file_path' or "
        "'obo_client_secret'!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
            interactive_client_id="123",
            client_id="123",
            obo_client_secret="secret-key",
        )

    with pytest.raises(
        ValueError,
        match="Pass exactly one of 'interactive_client_id', 'client_id', 'token_file_path' or "
        "'obo_client_secret'!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
            interactive_client_id="123",
            token_file_path=Path(),
            obo_client_secret="secret-key",
        )

    with pytest.raises(
        ValueError,
        match="Pass exactly one of 'interactive_client_id', 'client_id', 'token_file_path' or "
        "'obo_client_secret'!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
            client_id="123",
            token_file_path=Path(),
            obo_client_secret="secret-key",
        )

    with pytest.raises(
        ValueError,
        match="Pass exactly one of 'interactive_client_id', 'client_id', 'token_file_path' or "
        "'obo_client_secret'!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
            interactive_client_id="123",
            client_id="123",
            token_file_path=Path(),
            obo_client_secret="secret-key",
        )


def test_cognite_settings_interactive_client_id_missing_tenant_id():
    with pytest.raises(
        ValueError,
        match="'tenant_id' is required!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
            interactive_client_id="123",
        )


def test_cognite_settings_interactive_client_id_success():
    settings = CogniteSettings(
        base_url="https://t2ps.cognitedata.com",
        project="proj",
        client_name="t2psclient",
        interactive_client_id="123",
        tenant_id="456",
    )

    assert settings.base_url == "https://t2ps.cognitedata.com"
    assert settings.project == "proj"
    assert settings.client_name == "t2psclient"
    assert settings.interactive_client_id == "123"
    assert settings.client_id is None
    assert settings.client_secret is None
    assert settings.tenant_id == "456"
    assert settings.token_file_path is None
    assert settings.obo_client_secret is None


def test_cognite_settings_client_id_missing_secret_and_tenant_id():
    with pytest.raises(
        ValueError,
        match="'client_secret' is required!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
            client_id="123",
        )


def test_cognite_settings_client_id_missing_tenant_id():
    with pytest.raises(
        ValueError,
        match="'tenant_id' is required!",
    ):
        CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            project="proj",
            client_name="t2psclient",
            client_id="123",
            client_secret=SecretStr("secret-key"),
        )


def test_cognite_settings_client_id_success():
    settings = CogniteSettings(
        base_url="https://t2ps.cognitedata.com",
        project="proj",
        client_name="t2psclient",
        client_id="123",
        client_secret=SecretStr("secret-key"),
        tenant_id="456",
    )

    assert settings.base_url == "https://t2ps.cognitedata.com"
    assert settings.project == "proj"
    assert settings.client_name == "t2psclient"
    assert settings.interactive_client_id is None
    assert settings.client_id == "123"
    assert settings.client_secret.get_secret_value() == "secret-key"
    assert settings.tenant_id == "456"
    assert settings.token_file_path is None
    assert settings.obo_client_secret is None


def test_cognite_settings_token_file_path_success():
    settings = CogniteSettings(
        base_url="https://t2ps.cognitedata.com",
        project="proj",
        client_name="t2psclient",
        token_file_path=Path(),
    )

    assert settings.base_url == "https://t2ps.cognitedata.com"
    assert settings.project == "proj"
    assert settings.client_name == "t2psclient"
    assert settings.interactive_client_id is None
    assert settings.client_id is None
    assert settings.client_secret is None
    assert settings.tenant_id is None
    assert settings.token_file_path == Path()
    assert settings.obo_client_secret is None


def test_cognite_settings_obo_client_secret_success():
    settings = CogniteSettings(
        base_url="https://t2ps.cognitedata.com",
        project="proj",
        client_name="t2psclient",
        obo_client_secret=SecretStr("secret-key"),
    )

    assert settings.base_url == "https://t2ps.cognitedata.com"
    assert settings.project == "proj"
    assert settings.client_name == "t2psclient"
    assert settings.interactive_client_id is None
    assert settings.client_id is None
    assert settings.client_secret is None
    assert settings.tenant_id is None
    assert settings.token_file_path is None
    assert settings.obo_client_secret.get_secret_value() == "secret-key"


def test_cognite_settings_client_secret_env_prefix_loading():
    with patch.dict(
        os.environ,
        {
            "COGNITE_CLIENT_SECRET": "secret-key",
        },
    ):
        settings = CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
            client_id="123",
            tenant_id="456",
        )

        assert settings.base_url == "https://t2ps.cognitedata.com"
        assert settings.project == "prod"
        assert settings.client_name == "talk2powersystem"
        assert settings.interactive_client_id is None
        assert settings.client_id == "123"
        assert settings.client_secret.get_secret_value() == "secret-key"
        assert settings.tenant_id == "456"
        assert settings.token_file_path is None
        assert settings.obo_client_secret is None


def test_cognite_settings_obo_client_secret_env_prefix_loading():
    with patch.dict(
        os.environ,
        {
            "COGNITE_OBO_CLIENT_SECRET": "secret-key",
        },
    ):
        settings = CogniteSettings(
            base_url="https://t2ps.cognitedata.com",
        )

        assert settings.base_url == "https://t2ps.cognitedata.com"
        assert settings.project == "prod"
        assert settings.client_name == "talk2powersystem"
        assert settings.interactive_client_id is None
        assert settings.client_id is None
        assert settings.client_secret is None
        assert settings.tenant_id is None
        assert settings.token_file_path is None
        assert settings.obo_client_secret.get_secret_value() == "secret-key"
