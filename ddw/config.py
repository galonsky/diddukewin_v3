import os
from typing import Optional

import boto3

client = boto3.client("ssm")


def should_tweet() -> bool:
    return bool(os.getenv("TWEETING_ENABLED"))


class SSMConfig:
    def __init__(self):
        self._config = None

    def get_config(self, ssm_parameter_path="/ddw") -> dict:
        if self._config:
            return self._config
        # Get all parameters for this app
        param_details = client.get_parameters_by_path(
            Path=ssm_parameter_path, Recursive=False, WithDecryption=True
        )

        if "Parameters" in param_details and len(param_details.get("Parameters")) > 0:
            self._config = {}
            for param in param_details.get("Parameters"):
                param_path_array = param.get("Name").split("/")
                key = param_path_array[-1]
                value = param.get("Value")
                self._config[key] = value
            return self._config
        return {}

    def get_config_value(self, key: str) -> Optional[str]:
        return self.get_config().get(key)


ssm_config = SSMConfig()


def get_config_value(key: str) -> Optional[str]:
    return ssm_config.get_config_value(key)
