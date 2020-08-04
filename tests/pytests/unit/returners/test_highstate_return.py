import io

# import pytest
import salt.returners.highstate_return as highstate_return

# from tests.support.helpers import TstSuiteLoggingHandler
# from tests.support.mock import MagicMock, patch

# TODO: do we need this?
# @pytest.fixture(autouse=True)
# def setup_loader(request):
#    setup_loader_modules = {highstate_return: {}}
#    with pytest.helpers.loader_mock(request, setup_loader_modules) as loader_mock:
#        yield loader_mock


def test_generate_table_should_correctly_escape_html_characters_when_data_contains_both_list_and_dict():
    unescaped_fnord = "&fnord&"
    unescaped_dronf = "<dronf>"
    expected_escaped_fnord = "&amp;fnord&amp;"
    expected_escaped_dronf = "&lt;dronf&gt;"
    data = [["something", "or", "another", unescaped_fnord, {"cool": unescaped_dronf}]]

    out = io.StringIO()
    highstate_return._generate_html_table(data=data, out=out)
    out.seek(0)
    actual_table = out.read()

    assert expected_escaped_fnord in actual_table
    assert expected_escaped_dronf in actual_table
