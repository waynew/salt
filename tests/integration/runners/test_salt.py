# -*- coding: utf-8 -*-
"""
Tests for the salt runner

.. versionadded:: 2016.11.0
"""
# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals

import pytest

# Import Salt Testing libs
from tests.support.case import ShellCase


class SaltRunnerTest(ShellCase):
    """
    Test the salt runner
    """

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    def test_salt_cmd(self):
        """
        test return values of salt.cmd
        """
        ret = self.run_run_plus("salt.cmd", "test.ping")
        out_ret = ret.get("out")[0]
        return_ret = ret.get("return")

        self.assertEqual(out_ret, "True")
        self.assertTrue(return_ret)

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    def test_salt_cmd_invalid(self):
        """
        test return values of salt.cmd invalid parameters
        """
        ret = self.run_run_plus("salt.cmd")
        expected = "Passed invalid arguments:"
        self.assertIn(expected, ret["return"])
