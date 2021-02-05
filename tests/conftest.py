import pytest

from ddw.config import SSMConfig


@pytest.fixture(autouse=True)
def mock_ssm_config(mocker):
    mocker.patch.object(SSMConfig, "get_config", return_value={})
