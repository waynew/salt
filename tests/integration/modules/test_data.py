# -*- coding: utf-8 -*-

# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals

import pytest

# Import Salt Testing libs
from tests.support.case import ModuleCase


class DataModuleTest(ModuleCase):
    """
    Validate the data module
    """

    def setUp(self):
        self.run_function("data.clear")
        self.addCleanup(self.run_function, "data.clear")

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    @pytest.mark.slow_30
    def test_load_dump(self):
        """
        data.load
        data.dump
        """
        self.assertTrue(self.run_function("data.dump", ['{"foo": "bar"}']))
        self.assertEqual(self.run_function("data.load"), {"foo": "bar"})

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    @pytest.mark.slow_30
    @pytest.mark.slow_60
    def test_get_update(self):
        """
        data.get
        data.update
        """
        self.assertTrue(self.run_function("data.update", ["spam", "eggs"]))
        self.assertEqual(self.run_function("data.get", ["spam"]), "eggs")

        self.assertTrue(self.run_function("data.update", ["unladen", "swallow"]))
        self.assertEqual(
            self.run_function("data.get", [["spam", "unladen"]]), ["eggs", "swallow"]
        )

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    @pytest.mark.slow_30
    def test_cas_update(self):
        """
        data.update
        data.cas
        data.get
        """
        self.assertTrue(self.run_function("data.update", ["spam", "eggs"]))
        self.assertTrue(self.run_function("data.cas", ["spam", "green", "eggs"]))
        self.assertEqual(self.run_function("data.get", ["spam"]), "green")
