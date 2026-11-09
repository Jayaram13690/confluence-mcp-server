import os

from azure.appconfiguration.provider import (
    SettingSelector,
    load,
)
from azure.identity import DefaultAzureCredential


class AppConfigReader:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_APPCONFIG_ENDPOINT")
        self.app_name = os.getenv("APP_NAME", "confluence-mcp")
        self.environment = os.getenv("ENVIRONMENT", "dev")

    def load(self) -> dict:
        if not self.endpoint:
            return {}

        credential = DefaultAzureCredential()

        prefix = f"{self.app_name}:"

        config = load(
            endpoint=self.endpoint,
            credential=credential,
            selects=[
                SettingSelector(
                    key_filter=f"{prefix}*",
                    label_filter=self.environment,
                )
            ],
            trim_prefixes=[prefix],
            keyvault_credential=credential,
        )

        return dict(config)