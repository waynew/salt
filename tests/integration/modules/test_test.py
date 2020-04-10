# -*- coding: utf-8 -*-

# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals

import pytest
import salt.config

# Import salt libs
import salt.version

# Import Salt Testing libs
from tests.support.case import ModuleCase
from tests.support.mixins import AdaptedConfigurationTestCaseMixin


class TestModuleTest(ModuleCase, AdaptedConfigurationTestCaseMixin):
    """
    Validate the test module
    """

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    def test_ping(self):
        """
        test.ping
        """
        self.assertTrue(self.run_function("test.ping"))

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    def test_echo(self):
        """
        test.echo
        """
        self.assertEqual(self.run_function("test.echo", ["text"]), "text")

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    def test_version(self):
        """
        test.version
        """
        self.assertEqual(
            self.run_function("test.version"), salt.version.__saltstack_version__.string
        )

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    def test_conf_test(self):
        """
        test.conf_test
        """
        self.assertEqual(self.run_function("test.conf_test"), "baz")

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    def test_get_opts(self):
        """
        test.get_opts
        """
        opts = salt.config.minion_config(self.get_config_file_path("minion"))
        self.assertEqual(
            self.run_function("test.get_opts")["cachedir"], opts["cachedir"]
        )

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    def test_cross_test(self):
        """
        test.cross_test
        """
        self.assertTrue(self.run_function("test.cross_test", ["test.ping"]))

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    def test_fib(self):
        """
        test.fib
        """
        self.assertEqual(self.run_function("test.fib", ["20"],)[0], 6765)

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    def test_collatz(self):
        """
        test.collatz
        """
        self.assertEqual(self.run_function("test.collatz", ["40"],)[0][-1], 2)

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    def test_outputter(self):
        """
        test.outputter
        """
        self.assertEqual(self.run_function("test.outputter", ["text"]), "text")
