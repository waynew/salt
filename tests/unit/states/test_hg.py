# -*- coding: utf-8 -*-
"""
    :codeauthor: Rahul Handay <rahulha@saltstack.com>
"""
# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals

import os

import pytest

# Import Salt Libs
from salt.states import hg

# Import Salt Testing Libs
from tests.support.mixins import LoaderModuleMockMixin
from tests.support.mock import MagicMock, patch
from tests.support.unit import TestCase


class HgTestCase(TestCase, LoaderModuleMockMixin):
    """
        Validate the svn state
    """

    def setup_loader_modules(self):
        return {hg: {}}

    @pytest.mark.slow_0_01
    def test_latest(self):
        """
            Test to Make sure the repository is cloned to
            the given directory and is up to date
        """
        ret = {"changes": {}, "comment": "", "name": "salt", "result": True}
        mock = MagicMock(return_value=True)
        with patch.object(hg, "_fail", mock):
            self.assertTrue(hg.latest("salt"))

        mock = MagicMock(side_effect=[False, True, False, False, False, False])
        with patch.object(os.path, "isdir", mock):
            mock = MagicMock(return_value=True)
            with patch.object(hg, "_handle_existing", mock):
                self.assertTrue(hg.latest("salt", target="c:\\salt"))

            with patch.dict(hg.__opts__, {"test": True}):
                mock = MagicMock(return_value=True)
                with patch.object(hg, "_neutral_test", mock):
                    self.assertTrue(hg.latest("salt", target="c:\\salt"))

            with patch.dict(hg.__opts__, {"test": False}):
                mock = MagicMock(return_value=True)
                with patch.object(hg, "_clone_repo", mock):
                    self.assertDictEqual(hg.latest("salt", target="c:\\salt"), ret)

    @pytest.mark.slow_0_01
    def test_latest_update_changes(self):
        """
            Test to make sure we don't update even if we have changes
        """
        ret = {"changes": {}, "comment": "", "name": "salt", "result": True}
        revision_mock = MagicMock(return_value="abcdef")
        pull_mock = MagicMock(return_value="Blah.")
        update_mock = MagicMock()

        with patch.dict(
            hg.__salt__,
            {
                "hg.revision": revision_mock,
                "hg.pull": pull_mock,
                "hg.update": update_mock,
            },
        ):
            mock = MagicMock(side_effect=[True, True])
            with patch.object(os.path, "isdir", mock):
                mock = MagicMock(return_value=True)
                with patch.dict(hg.__opts__, {"test": False}):
                    with patch.object(hg, "_clone_repo", mock):
                        self.assertDictEqual(
                            hg.latest("salt", target="c:\\salt", update_head=True), ret
                        )
                        assert update_mock.called

    def test_latest_no_update_changes(self):
        """
            Test to make sure we don't update even if we have changes
        """
        ret = {
            "changes": {},
            "comment": "Update is probably required but update_head=False so we will skip updating.",
            "name": "salt",
            "result": True,
        }
        revision_mock = MagicMock(return_value="abcdef")
        pull_mock = MagicMock(return_value="Blah.")
        update_mock = MagicMock()

        with patch.dict(
            hg.__salt__,
            {
                "hg.revision": revision_mock,
                "hg.pull": pull_mock,
                "hg.update": update_mock,
            },
        ):
            mock = MagicMock(side_effect=[True, True])
            with patch.object(os.path, "isdir", mock):
                mock = MagicMock(return_value=True)
                with patch.dict(hg.__opts__, {"test": False}):
                    with patch.object(hg, "_clone_repo", mock):
                        self.assertDictEqual(
                            hg.latest("salt", target="c:\\salt", update_head=False), ret
                        )
                        assert not update_mock.called

    @pytest.mark.slow_0_01
    @pytest.mark.slow_0_1
    def test_latest_no_update_no_changes(self):
        """
            Test to Make sure the repository is cloned to
            the given directory and is up to date
        """
        ret = {
            "changes": {},
            "comment": "No changes found and update_head=False so will skip updating.",
            "name": "salt",
            "result": True,
        }
        revision_mock = MagicMock(return_value="abcdef")
        pull_mock = MagicMock(return_value="Blah no changes found.")
        update_mock = MagicMock()

        with patch.dict(
            hg.__salt__,
            {
                "hg.revision": revision_mock,
                "hg.pull": pull_mock,
                "hg.update": update_mock,
            },
        ):
            mock = MagicMock(side_effect=[True, True])
            with patch.object(os.path, "isdir", mock):
                mock = MagicMock(return_value=True)
                with patch.dict(hg.__opts__, {"test": False}):
                    with patch.object(hg, "_clone_repo", mock):
                        self.assertDictEqual(
                            hg.latest("salt", target="c:\\salt", update_head=False), ret
                        )
                        assert not update_mock.called
