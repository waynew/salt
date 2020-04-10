# -*- coding: utf-8 -*-

# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals

import pytest

# Import Salt Libs
import salt.utils.platform

# Import Salt Testing Libs
from tests.support.case import SSHCase
from tests.support.unit import skipIf


@skipIf(salt.utils.platform.is_windows(), "salt-ssh not available on Windows")
class SSHPillarTest(SSHCase):
    """
    testing pillar with salt-ssh
    """

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    def test_pillar_items(self):
        """
        test pillar.items with salt-ssh
        """
        ret = self.run_function("pillar.items")
        self.assertDictContainsSubset({"monty": "python"}, ret)
        self.assertDictContainsSubset(
            {"knights": ["Lancelot", "Galahad", "Bedevere", "Robin"]}, ret
        )

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    def test_pillar_get(self):
        """
        test pillar.get with salt-ssh
        """
        ret = self.run_function("pillar.get", ["monty"])
        self.assertEqual(ret, "python")

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    @pytest.mark.slow_1
    @pytest.mark.slow_10
    def test_pillar_get_doesnotexist(self):
        """
        test pillar.get when pillar does not exist with salt-ssh
        """
        ret = self.run_function("pillar.get", ["doesnotexist"])
        self.assertEqual(ret, "")
