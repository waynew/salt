# -*- coding: utf-8 -*-
"""
Pillar include tests
"""
from __future__ import absolute_import, unicode_literals

import pytest
from tests.support.case import ModuleCase


class PillarIncludeTest(ModuleCase):
    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    def test_pillar_include(self):
        """
        Test pillar include
        """
        ret = self.minion_run("pillar.items")
        assert "a" in ret["element"]
        assert ret["element"]["a"] == {"a": ["Entry A"]}
        assert "b" in ret["element"]
        assert ret["element"]["b"] == {"b": ["Entry B"]}

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    def test_pillar_glob_include(self):
        """
        Test pillar include via glob pattern
        """
        ret = self.minion_run("pillar.items")
        assert "glob-a" in ret
        assert ret["glob-a"] == ["Entry A"]
        assert "glob-b" in ret
        assert ret["glob-b"] == ["Entry B"]
