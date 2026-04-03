import os
from unittest.mock import patch

import pytest
from pydantic import SecretStr

from talk2powersystemllm.agent import LLMSettings, LLMType


def test_llm_settings_openai_success():
    settings = LLMSettings(
        type=LLMType.openai,
        model="gpt-4o",
        api_key=SecretStr("secret-key"),
    )
    assert settings.type == LLMType.openai
    assert settings.model == "gpt-4o"
    assert settings.azure_endpoint is None
    assert settings.api_version is None
    assert settings.hugging_face_endpoint is None
    assert settings.temperature == 0
    assert settings.use_responses_api is None
    assert settings.seed is None
    assert settings.timeout == 120
    assert settings.api_key.get_secret_value() == "secret-key"


def test_llm_settings_default_azure_success():
    settings = LLMSettings(
        model="gpt-4o",
        azure_endpoint="https://example.openai.azure.com",
        api_version="2024-02-15-preview",
        api_key=SecretStr("secret-key"),
    )
    assert settings.type == LLMType.azure_openai
    assert settings.model == "gpt-4o"
    assert settings.azure_endpoint == "https://example.openai.azure.com"
    assert settings.api_version == "2024-02-15-preview"
    assert settings.hugging_face_endpoint is None
    assert settings.temperature == 0
    assert settings.use_responses_api is None
    assert settings.seed is None
    assert settings.timeout == 120
    assert settings.api_key.get_secret_value() == "secret-key"


def test_llm_settings_azure_missing_endpoint_and_version():
    with pytest.raises(ValueError, match="azure_endpoint is required!"):
        LLMSettings(
            model="gpt-4o",
            api_key=SecretStr("secret-key"),
        )


def test_llm_settings_azure_missing_endpoint():
    with pytest.raises(ValueError, match="azure_endpoint is required!"):
        LLMSettings(
            model="gpt-4o",
            api_version="2024-02-15-preview",
            api_key=SecretStr("secret-key"),
        )


def test_llm_settings_azure_missing_version():
    with pytest.raises(ValueError, match="api_version is required!"):
        LLMSettings(
            model="gpt-4o",
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
    with pytest.raises(ValueError, match="seed` is not supported by the Responses API"):
        LLMSettings(
            model="gpt-4o",
            azure_endpoint="https://example.openai.azure.com",
            api_version="2024-02-15-preview",
            use_responses_api=True,
            seed=0,
            api_key=SecretStr("secret-key"),
        )

    with pytest.raises(ValueError, match="seed` is not supported by the Responses API"):
        LLMSettings(
            model="gpt-4o",
            azure_endpoint="https://example.openai.azure.com",
            api_version="2024-02-15-preview",
            use_responses_api=True,
            seed=42,
            api_key=SecretStr("secret-key"),
        )

    with pytest.raises(ValueError, match="seed` is not supported by the Responses API"):
        LLMSettings(
            type=LLMType.openai,
            model="gpt-4o",
            use_responses_api=True,
            seed=0,
            api_key=SecretStr("secret-key"),
        )

    with pytest.raises(ValueError, match="seed` is not supported by the Responses API"):
        LLMSettings(
            type=LLMType.openai,
            model="gpt-4o",
            use_responses_api=True,
            seed=42,
            api_key=SecretStr("secret-key"),
        )


def test_llm_settings_responses_api_without_seed_success():
    settings = LLMSettings(
        model="gpt-4o",
        azure_endpoint="https://example.openai.azure.com",
        api_version="2024-02-15-preview",
        use_responses_api=True,
        api_key=SecretStr("secret-key"),
    )
    assert settings.type == LLMType.azure_openai
    assert settings.model == "gpt-4o"
    assert settings.azure_endpoint == "https://example.openai.azure.com"
    assert settings.api_version == "2024-02-15-preview"
    assert settings.hugging_face_endpoint is None
    assert settings.temperature == 0
    assert settings.use_responses_api
    assert settings.seed is None
    assert settings.timeout == 120
    assert settings.api_key.get_secret_value() == "secret-key"

    settings = LLMSettings(
        type=LLMType.openai,
        model="gpt-4o",
        use_responses_api=True,
        api_key=SecretStr("secret-key"),
    )
    assert settings.type == LLMType.openai
    assert settings.model == "gpt-4o"
    assert settings.azure_endpoint is None
    assert settings.api_version is None
    assert settings.hugging_face_endpoint is None
    assert settings.temperature == 0
    assert settings.use_responses_api
    assert settings.seed is None
    assert settings.timeout == 120
    assert settings.api_key.get_secret_value() == "secret-key"


def test_llm_settings_env_prefix_loading():
    with patch.dict(
        os.environ,
        {
            "LLM_MODEL": "gpt-4o",
            "LLM_AZURE_ENDPOINT": "https://example.openai.azure.com",
            "LLM_API_VERSION": "2024-02-15-preview",
            "LLM_API_KEY": "secret-key",
        },
    ):
        settings = LLMSettings()
        assert settings.type == LLMType.azure_openai
        assert settings.model == "gpt-4o"
        assert settings.azure_endpoint == "https://example.openai.azure.com"
        assert settings.api_version == "2024-02-15-preview"
        assert settings.hugging_face_endpoint is None
        assert settings.temperature == 0
        assert settings.use_responses_api is None
        assert settings.seed is None
        assert settings.timeout == 120
        assert settings.api_key.get_secret_value() == "secret-key"


def test_llm_settings_temperature_range_validation():
    with pytest.raises(ValueError):
        LLMSettings(
            model="gpt-4o",
            azure_endpoint="https://example.openai.azure.com",
            api_version="2024-02-15-preview",
            temperature=2.1,
            use_responses_api=True,
            api_key=SecretStr("secret-key"),
        )

    with pytest.raises(ValueError):
        LLMSettings(
            model="gpt-4o",
            azure_endpoint="https://example.openai.azure.com",
            api_version="2024-02-15-preview",
            temperature=-0.1,
            use_responses_api=True,
            api_key=SecretStr("secret-key"),
        )


def test_llm_settings_timeout_range_validation():
    with pytest.raises(ValueError):
        LLMSettings(
            model="gpt-4o",
            azure_endpoint="https://example.openai.azure.com",
            api_version="2024-02-15-preview",
            timeout=0,
            use_responses_api=True,
            api_key=SecretStr("secret-key"),
        )

    with pytest.raises(ValueError):
        LLMSettings(
            model="gpt-4o",
            azure_endpoint="https://example.openai.azure.com",
            api_version="2024-02-15-preview",
            timeout=-1,
            use_responses_api=True,
            api_key=SecretStr("secret-key"),
        )
