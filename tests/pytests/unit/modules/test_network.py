import pytest
import salt.modules.network as network
import salt.utils.stringutils
import salt.utils.path
import salt.utils.platform
from tests.support.helpers import TstSuiteLoggingHandler
from tests.support.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def setup_loader():
    setup_loader_modules = {network: {"__utils__":{
        'stringutils.is_quoted': salt.utils.stringutils.is_quoted,
        'path.which': salt.utils.path.which,
        'platform.is_sunos': salt.utils.platform.is_sunos,
    }}, }
    with pytest.helpers.loader_mock(setup_loader_modules) as loader_mock:
        yield loader_mock


@pytest.fixture
def extra_patches():
    with patch.dict(network.__salt__, {'cmd.run_all': MagicMock(return_value={'retcode': 0, 'stdout': 'hello'})}):
        yield


def test_when_redhat_network_has_double_quotes_then_hostname_should_be_correct(extra_patches):
    network.mod_hostname('bloop')
    ...

def test_when_redhat_network_has_single_quote_then_hostname_should_be_correct():
    ...

def test_when_redhat_network_is_unquoted_then_hostname_should_be_correct():
    ...

