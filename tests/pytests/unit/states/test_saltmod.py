# -*- coding: utf-8 -*-

import pytest
import salt.modules.saltutil as saltutil
import salt.states.saltmod as saltmod
from tests.support.mock import create_autospec, patch


@pytest.fixture(autouse=True)
def setup_loader(request):
    setup_loader_modules = {saltmod: {}}
    with pytest.helpers.loader_mock(request, setup_loader_modules) as loader_mock:
        yield loader_mock


@pytest.mark.parametrize(
    "exclude", [True, False],
)
def test_exclude_parameter_gets_passed(exclude):
    """ Smoke test for for salt.states.statemod.state().  Ensures that we
        don't take an exception if optional parameters are not specified in
        __opts__ or __env__.
    """
    args = ("webserver_setup", "webserver2")
    expected_exclude = exclude
    kwargs = {
        "tgt_type": "glob",
        "exclude": expected_exclude,
        "highstate": True,
    }
    fake_cmd = create_autospec(saltutil.cmd)
    with patch.dict(saltmod.__salt__, {"saltutil.cmd": fake_cmd}), patch.dict(
        saltmod.__opts__, {"__role": "testsuite"}
    ):
        saltmod.state(*args, **kwargs)

        call = fake_cmd.call_args[1]
        assert call["kwarg"]["exclude"] == expected_exclude
