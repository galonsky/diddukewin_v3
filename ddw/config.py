import os
from time import time
from typing import Optional

from ddw.aws import ssm

CONFIG_TTL_SECONDS = 60


def should_tweet() -> bool:
    return bool(os.getenv("TWEETING_ENABLED"))


class SSMConfig:
    def __init__(self):
        self._config = None
        self._last_fetched = None

    def get_config(self, ssm_parameter_path="/ddw") -> dict:
        if self._config and (
            self._last_fetched and (time() - self._last_fetched) < CONFIG_TTL_SECONDS
        ):
            return self._config
        # Get all parameters for this app
        param_details = ssm.get_parameters_by_path(
            Path=ssm_parameter_path, Recursive=False, WithDecryption=True
        )

        if "Parameters" in param_details and len(param_details.get("Parameters")) > 0:
            self._config = {}
            for param in param_details.get("Parameters"):
                param_path_array = param.get("Name").split("/")
                key = param_path_array[-1]
                value = param.get("Value")
                self._config[key] = value
            self._last_fetched = time()
            return self._config
        return {}

    def get_config_value(self, key: str) -> Optional[str]:
        return self.get_config().get(key)


ssm_config = SSMConfig()


def get_config_value(key: str) -> Optional[str]:
    return ssm_config.get_config_value(key)
