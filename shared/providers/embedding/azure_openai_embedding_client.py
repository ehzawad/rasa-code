import os
from typing import Any, Dict, List, Optional

import structlog

from rasa.shared.constants import (
    API_BASE_CONFIG_KEY,
    API_KEY,
    API_VERSION_CONFIG_KEY,
    AZURE_API_BASE_ENV_VAR,
    AZURE_API_KEY_ENV_VAR,
    AZURE_API_TYPE_ENV_VAR,
    AZURE_API_VERSION_ENV_VAR,
    AZURE_OPENAI_PROVIDER,
    OPENAI_API_BASE_ENV_VAR,
    OPENAI_API_KEY_ENV_VAR,
    OPENAI_API_TYPE_ENV_VAR,
    OPENAI_API_VERSION_ENV_VAR,
)
from rasa.shared.exceptions import ProviderClientValidationError
from rasa.shared.providers._configs.azure_openai_client_config import (
    AzureEntraIDOAuthConfig,
    AzureOpenAIClientConfig,
)
from rasa.shared.providers.constants import (
    DEFAULT_AZURE_API_KEY_NAME,
    LITE_LLM_API_KEY_FIELD,
    LITE_LLM_AZURE_AD_TOKEN,
)
from rasa.shared.providers.embedding._base_litellm_embedding_client import (
    _BaseLiteLLMEmbeddingClient,
)
from rasa.shared.utils.io import raise_deprecation_warning

structlogger = structlog.get_logger()


class AzureOpenAIEmbeddingClient(_BaseLiteLLMEmbeddingClient):
    """A client for interfacing with Azure's OpenAI embedding deployments.

    Parameters:
        deployment (str): The deployment name.
        model (Optional[str]): The embedding model name.
        api_base (Optional[str]): The base URL for the API endpoints.
            If not provided, it will be set via environment variable.
        api_type (Optional[str]): The type of the API to use.
            If not provided, it will be set via environment variable.
        api_version (Optional[str]): The version of the API to use.
            If not provided, it will be set via environment variable.
        oauth (Optional[AzureEntraIDOAuthConfig]): Optional OAuth configuration.
            If provided, the client will use OAuth for authentication.
        kwargs (Optional[Dict[str, Any]]): Optional configuration parameters specific
            to the embedding model deployment.

    Raises:
        ProviderClientValidationError: If validation of the client setup fails.
        DeprecationWarning: If deprecated environment variables are used for
            configuration.
    """

    def __init__(
        self,
        deployment: str,
        model: Optional[str] = None,
        api_base: Optional[str] = None,
        api_type: Optional[str] = None,
        api_version: Optional[str] = None,
        oauth: Optional[AzureEntraIDOAuthConfig] = None,
        **kwargs: Any,
    ):
        super().__init__()  # type: ignore
        self._deployment = deployment
        self._model = model
        self._extra_parameters = kwargs or {}

        # Set api_base with the following priority:
        # parameter -> Azure Env Var -> (deprecated) OpenAI Env Var
        self._api_base = (
            api_base
            or os.environ.get(AZURE_API_BASE_ENV_VAR)
            or os.environ.get(OPENAI_API_BASE_ENV_VAR)
        )
        self._api_type = (
            api_type
            or os.environ.get(AZURE_API_TYPE_ENV_VAR)
            or os.environ.get(OPENAI_API_TYPE_ENV_VAR)
        )
        self._api_version = (
            api_version
            or os.environ.get(AZURE_API_VERSION_ENV_VAR)
            or os.environ.get(OPENAI_API_VERSION_ENV_VAR)
        )
        # Litellm does not support use of OPENAI_API_KEY, so we need to map it
        # because of backward compatibility. However, we're first looking at
        # AZURE_API_KEY.

        self._oauth = oauth
        self._api_key_env_var = (
            self._resolve_api_key_env_var() if not self._oauth else None
        )

        self.validate_client_setup()

    def _resolve_api_key_env_var(self) -> str:
        """Resolves the environment variable to use for the API key.

        Returns:
            str: The env variable in dollar syntax format to use for the API key.
        """
        if API_KEY in self._extra_parameters:
            # API key is set to an env var in the config itself
            # in case the model is defined in the endpoints.yml
            return self._extra_parameters[API_KEY]

        if os.getenv(AZURE_API_KEY_ENV_VAR) is not None:
            return f"${{{DEFAULT_AZURE_API_KEY_NAME}}}"

        if os.getenv(OPENAI_API_KEY_ENV_VAR) is not None:
            # API key can be set through OPENAI_API_KEY too,
            # because of the backward compatibility
            raise_deprecation_warning(
                message=(
                    f"Usage of '{OPENAI_API_KEY_ENV_VAR}' environment variable "
                    "for setting the API key of "
                    "Azure OpenAI client is deprecated and will "
                    "be removed in 4.0.0. Please "
                    f"use '{AZURE_API_KEY_ENV_VAR}' instead."
                )
            )
            return "${OPENAI_API_KEY}"

        structlogger.error(
            "azure_openai_embedding_client.api_key_not_set",
            event_info=(
                "API key not set, it is required for API calls. "
                f"Set it either via the environment variable "
                f"'{AZURE_API_KEY_ENV_VAR}' or directly"
                f"via the config key '{API_KEY}'."
            ),
        )
        raise ProviderClientValidationError(
            f"Missing required environment variable/config key '{API_KEY}' for "
            f"API calls."
        )

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "AzureOpenAIEmbeddingClient":
        """Initializes the client from given configuration.

        Args:
            config (Dict[str, Any]): Configuration.

        Raises:
            ValueError: Raised in cases of invalid configuration:
                - If any of the required configuration keys are missing.
                - If `api_type` has a value different from `azure`.

        Returns:
            AzureOpenAIEmbeddingClient: Initialized client.
        """
        try:
            azure_openai_config = AzureOpenAIClientConfig.from_dict(config)
        except ValueError as e:
            message = "Cannot instantiate a client from the passed configuration."
            structlogger.error(
                "azure_openai_embedding_client.from_config.error",
                message=message,
                config=config,
                original_error=e,
            )
            raise

        return cls(
            deployment=azure_openai_config.deployment,
            model=azure_openai_config.model,
            api_base=azure_openai_config.api_base,
            api_type=azure_openai_config.api_type,
            api_version=azure_openai_config.api_version,
            oauth=azure_openai_config.oauth,
            **azure_openai_config.extra_parameters,
        )

    @property
    def config(self) -> dict:
        """Returns the configuration for that the llm client
        in dictionary form.
        """
        config = AzureOpenAIClientConfig(
            deployment=self.deployment,
            model=self.model,
            api_base=self.api_base,
            api_type=self.api_type,
            api_version=self.api_version,
            oauth=self._oauth,
            extra_parameters=self._extra_parameters,
        )
        return config.to_dict()

    @property
    def model(self) -> Optional[str]:
        """Returns the name of the model deployed on Azure. If model name is not
        provided, returns "N/A".
        """
        return self._model

    @property
    def deployment(self) -> str:
        """Return the deployment name for the azure openai embedding client."""
        return self._deployment

    @property
    def api_base(self) -> Optional[str]:
        """Returns the base API URL for the oazure penai embedding client."""
        return self._api_base

    @property
    def api_type(self) -> Optional[str]:
        """Returns the API type for the azure openai embedding client."""
        return self._api_type

    @property
    def api_version(self) -> Optional[str]:
        """Returns the API version for the azure openai embedding client."""
        return self._api_version

    @property
    def _litellm_extra_parameters(self) -> Dict[str, Any]:
        """Returns the model parameters for the azure openai embedding client.

        Returns:
            Dictionary containing the model parameters.
        """
        return self._extra_parameters

    @property
    def _embedding_fn_args(self) -> dict:
        auth_parameter: Dict[str, str] = {}

        if self._oauth:
            auth_parameter = {
                **auth_parameter,
                LITE_LLM_AZURE_AD_TOKEN: self._oauth.get_bearer_token(),
            }
        elif self._api_key_env_var:
            auth_parameter = {LITE_LLM_API_KEY_FIELD: self._api_key_env_var}

        return {
            **self._litellm_extra_parameters,
            "model": self._litellm_model_name,
            "api_base": self.api_base,
            "api_type": self.api_type,
            "api_version": self.api_version,
            **auth_parameter,
        }

    @property
    def _litellm_model_name(self) -> str:
        """Get the model name formatted for azure openai embedding client."""
        if self.deployment and f"{AZURE_OPENAI_PROVIDER}/" not in self.deployment:
            return f"{AZURE_OPENAI_PROVIDER}/{self.deployment}"
        return self.deployment

    def validate_client_setup(self) -> None:
        """Perform client validation.

        By default, only environment variables are validated.

        Raises:
            ProviderClientValidationError if validation fails.

        Throws:
            DeprecationWarning: If deprecated environment variables are used.
        """
        _substitute_env_key_mapper = [
            {
                "param_name": "API base",
                "config_key": API_BASE_CONFIG_KEY,
                "deprecated_env_key": OPENAI_API_BASE_ENV_VAR,
                "current_value": self.api_base,
                "new_env_key": AZURE_API_BASE_ENV_VAR,
            },
            {
                "param_name": "API version",
                "config_key": API_VERSION_CONFIG_KEY,
                "deprecated_env_key": OPENAI_API_VERSION_ENV_VAR,
                "current_value": self.api_version,
                "new_env_key": AZURE_API_VERSION_ENV_VAR,
            },
        ]

        self._throw_deprecation_warnings(_substitute_env_key_mapper)
        self._validate_client_setup(_substitute_env_key_mapper)

    def _throw_deprecation_warnings(self, mappings: List[Dict[str, Any]]) -> None:
        """Throw deprecation warnings for deprecated environment variables."""
        for mapping in mappings:
            # Value was set through the new environment variable
            if os.environ.get(mapping["new_env_key"]) is not None and mapping[
                "current_value"
            ] == os.environ.get(mapping["new_env_key"]):
                continue

            # Value was set through the deprecated environment variable
            if mapping["current_value"] == os.environ.get(
                mapping["deprecated_env_key"]
            ):
                raise_deprecation_warning(
                    message=(
                        f"Usage of {mapping['deprecated_env_key']} environment "
                        f"variable for setting the {mapping['param_name']} of Azure "
                        f"OpenAI client is deprecated and will be removed in 4.0.0. "
                        f"Please use {mapping['new_env_key']} instead."
                    )
                )

    def _validate_client_setup(self, mappings: List[Dict[str, Any]]) -> None:
        """Validate environment variables for the client."""
        missing_environment_variable = False
        for mapping in mappings:
            if not mapping["current_value"]:
                event_info = (
                    f"Environment variable: {mapping['new_env_key']} or config key: "
                    f"{mapping['config_key']} is not set. Required for API calls. "
                )
                structlogger.error(
                    "azure_openai_embedding_client.validate_environment_variables",
                    event_info=event_info,
                    missing_environment_variable=mapping["new_env_key"],
                )
                missing_environment_variable = True

        if missing_environment_variable:
            raise ProviderClientValidationError(
                "Missing required environment variables/config keys for API calls."
            )
