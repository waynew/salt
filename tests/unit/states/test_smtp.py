# -*- coding: utf-8 -*-
"""
    :codeauthor: Jayesh Kariya <jayeshk@saltstack.com>
"""
# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals

import pytest

# Import Salt Libs
from salt.states import smtp

# Import Salt Testing Libs
from tests.support.mixins import LoaderModuleMockMixin
from tests.support.mock import MagicMock, patch
from tests.support.unit import TestCase


class SmtpTestCase(TestCase, LoaderModuleMockMixin):
    """
    Test cases for salt.states.smtp
    """

    def setup_loader_modules(self):
        return {smtp: {}}

    # 'send_msg' function tests: 1

    @pytest.mark.slow_0_01
    def test_send_msg(self):
        """
        Test to send a message via SMTP
        """
        name = "This is a salt states module"

        comt = (
            "Need to send message to admin@example.com:" " This is a salt states module"
        )

        ret = {"name": name, "changes": {}, "result": None, "comment": comt}

        with patch.dict(smtp.__opts__, {"test": True}):
            self.assertDictEqual(
                smtp.send_msg(
                    name,
                    "admin@example.com",
                    "Message from Salt",
                    "admin@example.com",
                    "my-smtp-account",
                ),
                ret,
            )

        comt = "Sent message to admin@example.com: " "This is a salt states module"

        with patch.dict(smtp.__opts__, {"test": False}):
            mock = MagicMock(return_value=True)
            with patch.dict(smtp.__salt__, {"smtp.send_msg": mock}):
                ret["comment"] = comt
                ret["result"] = True
                self.assertDictEqual(
                    smtp.send_msg(
                        name,
                        "admin@example.com",
                        "Message from Salt",
                        "admin@example.com",
                        "my-smtp-account",
                    ),
                    ret,
                )
