# -*- coding: utf-8 -*-

# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals

import re

import pytest

# Import Salt Testing libs
from tests.support.case import ModuleCase


class KeyModuleTest(ModuleCase):
    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    def test_key_finger(self):
        """
        test key.finger to ensure we receive a valid fingerprint
        """
        out = self.run_function("key.finger")
        match = re.match("([0-9a-z]{2}:){15,}[0-9a-z]{2}$", out)
        self.assertTrue(match)

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    def test_key_finger_master(self):
        """
        test key.finger_master to ensure we receive a valid fingerprint
        """
        out = self.run_function("key.finger_master")
        match = re.match("([0-9a-z]{2}:){15,}[0-9a-z]{2}$", out)
        self.assertTrue(match)
