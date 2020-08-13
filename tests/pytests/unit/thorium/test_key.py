import pytest
import salt.key
import salt.thorium.key as key
from tests.support.mock import MagicMock, create_autospec, patch


@pytest.fixture(autouse=True)
def setup_loader(request):
    setup_loader_modules = {key: {"__reg__": {}}}
    with pytest.helpers.loader_mock(request, setup_loader_modules) as loader_mock:
        yield loader_mock


# TODO: better name for this test function -W. Werner, 2020-08-13
def test_if_name_match_is_not_provided_then_something_something_something():
    fake_key = create_autospec(salt.key.Key, return_value=MagicMock())
    # TODO: create correct looking return value -W. Werner, 2020-08-13
    fake_key.return_value.list_status.return_value = [True]
    patch_key = patch("salt.key.Key", fake_key)
    # TODO: Patch reg with correct looking values -W. Werner, 2020-08-13
    patch_reg = patch.dict(key.__reg__, {"status": {"val": {42: {"recv_time": 100}}}})
    with patch_key, patch_reg:
        key.timeout(name="fnord")
        # TODO: add assertion - delete_key and reject_key should be called with correct data - -W. Werner, 2020-08-13
        calls = fake_key.return_value.delete_key.mock_calls
        args = calls[0].args[0]
        assert False, str(calls) + repr(args)


def test_when_timeout_is_called_with_name_match_and_no_keys_should_be_deleted_or_rejected_none_should_be():
    pytest.skip("write me!")
    # probably delete_key.assert_not_called() and reject.assert_not_called() - check mock assert methods


def test_when_timeout_is_called_with_name_match_and_keys_should_be_deleted_it_should_delete_correct_keys():
    pytest.skip("write me!")


def test_when_timeout_is_called_with_name_match_and_keys_should_be_reject_it_should_reject_correct_keys():
    pytest.skip("write me!")


def test_when_timeout_is_called_with_no_name_match_XXX():
    pytest.skip("write me too!")
    # should be basically the same as above, but instead of name_match, it should just do the regular type
