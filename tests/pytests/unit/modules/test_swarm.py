import pytest
import salt.modules.swarm as swarm
from tests.support.helpers import TstSuiteLoggingHandler
from tests.support.mock import MagicMock, patch, create_autospec, DEFAULT
import docker


@pytest.fixture(autouse=True)
def setup_loader(request):
    setup_loader_modules = {swarm: {"__context__": {}}}
    with pytest.helpers.loader_mock(request, setup_loader_modules) as loader_mock:
        yield loader_mock

@pytest.fixture
def fake_context_client():
    fake_client = MagicMock()
    patch_context = patch.dict(swarm.__context__, {'client': fake_client, 'server_name': "fakeo server"})
    patch_swarm_token = patch('salt.modules.swarm.swarm_tokens', autospec=True, return_value="Boop")
    with patch_context, patch_swarm_token:
        yield fake_client

def test_when_swarm_init_is_called_with_the_same_information_twice_it_should_return_expected_errors(fake_context_client):
    fake_context_client.swarm.init.side_effect = [DEFAULT, docker.errors.APIError('mah message', explanation="some explanation")]
    expected_good_result = {'comment': 'Docker swarm has been initialized'}
    expected_bad_result = {'comment': 'This node is already part of a swarm. Use "docker swarm leave" to leave this swarm and join another one.', 'result': True}

    first_result = swarm.swarm_init('127.0.0.1', '0.0.0.0', False)
    second_result = swarm.swarm_init('127.0.0.1', '0.0.0.0', False)

    print('xxx calls', fake_context_client.swarm.init.mock_calls)
    assert first_result == expected_good_result
    assert second_result == expected_bad_result

