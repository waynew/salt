# -*- coding: utf-8 -*-
"""
    :codeauthor: Rahul Handay <rahulha@saltstack.com>
"""

# Import Python Libs
from __future__ import absolute_import, print_function, unicode_literals

import pytest

# Import Salt Libs
from salt.modules import nfs3

# Import Salt Testing Libs
from tests.support.mixins import LoaderModuleMockMixin
from tests.support.mock import MagicMock, mock_open, patch
from tests.support.unit import TestCase


class NfsTestCase(TestCase, LoaderModuleMockMixin):
    """
    Test cases for salt.modules.nfs3
    """

    def setup_loader_modules(self):
        return {nfs3: {}}

    def test_list_exports(self):
        """
        Test for List configured exports
        """
        with patch("salt.utils.files.fopen", mock_open(read_data="A B1(23")):
            exports = nfs3.list_exports()
            assert exports == {"A": [{"hosts": "B1", "options": ["23"]}]}, exports

    @pytest.mark.slow_0_01
    def test_del_export(self):
        """
        Test for Remove an export
        """
        list_exports_mock = MagicMock(
            return_value={"A": [{"hosts": ["B1"], "options": ["23"]}]}
        )
        with patch.object(nfs3, "list_exports", list_exports_mock), patch.object(
            nfs3, "_write_exports", MagicMock(return_value=None)
        ):
            result = nfs3.del_export(path="A")
            assert result == {}, result
