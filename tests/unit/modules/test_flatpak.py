# -*- coding: utf-8 -*-
import salt.modules.flatpak as flatpak
from tests.support.mixins import LoaderModuleMockMixin
from tests.support.mock import MagicMock, patch
from tests.support.unit import TestCase


class TestFlatPack(TestCase, LoaderModuleMockMixin):
    def setup_loader_modules(self):
        return {flatpak: {}}

    def test_virtual_returns_false_when_flatpak_bin_no_on_path(self):
        expected_reason = (
            "The flatpak execution module cannot be loaded:"
            ' the "flatpak" binary is not in the path.'
        )
        with patch("salt.utils.path.which", return_value=False):
            result, reason = flatpak.__virtual__()
            self.assertFalse(result)
            self.assertEqual(reason, expected_reason)

    def test_virtual_returns_flatpak_name_when_flatpak_bin_is_on_path(self):
        expected_virtual_name = "flatpak is the coolest fnord"
        patch_which = patch("salt.utils.path.which", return_value=True)
        patch_virtual_name = patch(
            "salt.modules.flatpak.__virtualname__", expected_virtual_name
        )
        with patch_which, patch_virtual_name:
            result = flatpak.__virtual__()
            self.assertEqual(result, expected_virtual_name)

    def test_install_uses_correct_flatpak_command(self):
        expected_command = "NOT_REALLY_FLATPAK install fnord_location fnord_name"

        mock_runall = MagicMock()
        patch_flatpak_binary = patch(
            "salt.modules.flatpak.FLATPAK_BINARY_NAME", "NOT_REALLY_FLATPAK"
        )
        patch_runall = patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall})
        with patch_flatpak_binary, patch_runall:
            flatpak.install(location="fnord_location", name="fnord_name")
            command = mock_runall.call_args.args[0]
            self.assertEqual(command, expected_command)

    def test_install_should_fail_when_flatpak_returns_nonzero_and_stderr(self):
        ...

    def test_install_should_not_fail_when_flatpak_returns_zero_and_stderr(self):
        # Based on flapak code as of 2020-04-30 when there's an error
        # running flatpak it will return both nonzero and dump to stderr.
        # If this changes in the future, this test will need to be modified.
        ...

    def test_install_should_succed_when_flatpak_returns_zero_with_output(self):
        ...

    def test_install_should_succed_with_only_whitespace_output(self):
        ...
