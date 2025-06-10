import pytest

from autotrade.settings.config import set_config
from test.mocks.config import TestConfig


@pytest.fixture
def with_config():
    test_config = TestConfig()
    
    yield test_config

    test_config.reset()