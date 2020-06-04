# -*- coding: utf-8 -*-
import salt.modules.opsgenie as opsgeniemod
import salt.states.opsgenie as opsgenie
from tests.support.mixins import LoaderModuleMockMixin
from tests.support.mock import create_autospec, patch
from tests.support.unit import TestCase


class TestOpsGeneieState(TestCase, LoaderModuleMockMixin):
    def setup_loader_modules(self):
        fake_post_data = create_autospec(
            opsgeniemod.post_data, return_value=(42, "blarp")
        )
        return {
            opsgenie: {
                "__opts__": {"test": False},
                "__salt__": {"opsgenie.post_data": fake_post_data},
            }
        }

    def test_when_test_mode_then_changes_should_be_and_empty_dictionary(self):
        with patch.dict(opsgenie.__opts__, {"test": True}):
            result = opsgenie.create_alert(
                name="fnord", api_key="fnord", reason="fnord"
            )

            self.assertDictEqual(result["changes"], {})

    def test_when_opsgenie_response_code_is_in_200s_changes_should_be_an_empty_dictionary(
        self,
    ):
        opsgenie.__salt__["opsgenie.post_data"].return_value = (201, "fnord")
        with patch.dict(opsgenie.__opts__, {"test": False}):
            result = opsgenie.create_alert(
                name="fnord", api_key="fnord", reason="fnord"
            )

        self.assertDictEqual(result["changes"], {})

    def test_when_opsgenie_response_code_is_not_in_200s_changeds_should_be_an_empty_dictionary(
        self,
    ):
        # TODO: when we use pytest, pass in 199 and 300 at least for status codes (pytest.mark.parametrized) -W. Werner, 2020-06-04
        opsgenie.__salt__["opsgenie.post_data"].return_value = (300, "fnord")
        with patch.dict(opsgenie.__opts__, {"test": False}):
            result = opsgenie.create_alert(
                name="fnord", api_key="fnord", reason="fnord"
            )

            self.assertDictEqual(result["changes"], {})
