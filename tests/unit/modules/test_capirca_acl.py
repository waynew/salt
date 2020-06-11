# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from textwrap import dedent

import salt.modules.capirca_acl as capirca_acl
import salt.utils.path
from tests.support.mixins import LoaderModuleMockMixin
from tests.support.mock import MagicMock, patch
from tests.support.unit import TestCase


class TestCapircaACL(TestCase, LoaderModuleMockMixin):
    def setup_loader_modules(self):
        return {capirca_acl: {"__salt__": {"pillar.get": MagicMock()}}}

    def test_get_policy_config_should_return_expected_policy(self):
        expected_config = dedent(
            """
            ! $Date: 2019/12/13 $
            no ip access-list extended Internet-ACL-In
            ip access-list extended Internet-ACL-In
             remark log remaining Traffic
             deny ip any any log

            exit
        """
        )
        patch_pillar_get = patch.dict(
            capirca_acl.__salt__,
            {
                "pillar.get": MagicMock(
                    return_value={"fnord": ...}
                )  # TODO specific return
            },
        )
        with patch_pillar_get as mock_pillar:
            actual_config = capirca_acl.get_policy_config(
                "cisco"
            )  # TODO add correct args

            self.assertEqual(actual_config, expected_config)
