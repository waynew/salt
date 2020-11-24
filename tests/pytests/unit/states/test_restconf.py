import pytest
import salt.states.restconf as restconf
from tests.support.helpers import TstSuiteLoggingHandler
from tests.support.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def setup_loader():
    setup_loader_modules = {restconf: {}}
    with pytest.helpers.loader_mock(setup_loader_modules) as loader_mock:
        yield loader_mock


def test_mocking_dunder_salt():
    with patch.dict(restconf.__salt__, {"restconf.get_data": MagicMock(return_value="fnordy")}):
        assert restconf.removeme() == "fnord"
