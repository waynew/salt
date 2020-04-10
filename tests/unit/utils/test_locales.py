# coding: utf-8

# Import Python libs
from __future__ import absolute_import, unicode_literals

import pytest

# Import 3rd-part libs
from salt.ext.six.moves import reload_module

# Import Salt libs
from salt.utils import locales
from tests.support.mock import patch
from tests.support.unit import TestCase


class TestLocales(TestCase):
    @pytest.mark.slow_0_01
    def test_get_encodings(self):
        # reload locales modules before and after to defeat memoization of
        # get_encodings()
        reload_module(locales)
        with patch("sys.getdefaultencoding", return_value="xyzzy"):
            encodings = locales.get_encodings()
            for enc in (__salt_system_encoding__, "xyzzy", "utf-8", "latin-1"):
                self.assertIn(enc, encodings)
        reload_module(locales)

    def test_split_locale(self):
        self.assertDictEqual(
            locales.split_locale("ca_ES.UTF-8@valencia utf-8"),
            {
                "charmap": "utf-8",
                "modifier": "valencia",
                "codeset": "UTF-8",
                "language": "ca",
                "territory": "ES",
            },
        )

    def test_join_locale(self):
        self.assertEqual(
            locales.join_locale(
                {
                    "charmap": "utf-8",
                    "modifier": "valencia",
                    "codeset": "UTF-8",
                    "language": "ca",
                    "territory": "ES",
                }
            ),
            "ca_ES.UTF-8@valencia utf-8",
        )

    def test_normalize_locale(self):
        self.assertEqual(
            locales.normalize_locale("ca_es.UTF-8@valencia utf-8"),
            "ca_ES.utf8@valencia",
        )
