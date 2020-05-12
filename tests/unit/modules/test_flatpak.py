# -*- coding: utf-8 -*-
import textwrap

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
        # Based on flapak code as of 2020-04-30 when there's an error
        # running flatpak it will return both nonzero and dump to stderr.
        # If this changes in the future, this test will need to be modified.
        # arrange
        expected_stderr = "fnord"
        error_result = {"retcode": 1, "stderr": expected_stderr}
        mock_runall = MagicMock(return_value=error_result)

        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            # act
            result = flatpak.install(location="fnord_location", name="fnord_name")

            # assert
            self.assertFalse(result["result"])
            self.assertEqual(result["stderr"], expected_stderr)

    def test_install_should_not_fail_when_flatpak_returns_zero_and_stderr(self):
        expected_stdout = "some fnordy stdout"
        success_with_stderr = {
            "retcode": 0,
            "stderr": "some fnordy stderr",
            "stdout": expected_stdout,
        }
        mock_runall = MagicMock(return_value=success_with_stderr)
        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            result = flatpak.install(location="fnord_location", name="fnord_name")

            self.assertTrue(result["result"])
            self.assertEqual(result["stdout"], expected_stdout)

    def test_install_should_succed_when_flatpak_returns_zero_with_output(self):
        expected_stdout = "This is a fnordy stdout. There is something here."
        success_with_empty_output = {"retcode": 0, "stdout": expected_stdout}
        mock_runall = MagicMock(return_value=success_with_empty_output)
        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            result = flatpak.install(location="fnord_location", name="fnord_name")

            self.assertTrue(result["result"])
            self.assertEqual(result["stdout"], expected_stdout)

    def test_install_should_succed_with_only_whitespace_output(self):
        expected_stdout = ""
        all_the_whitespaces = "\n\t\t\n\f     "
        success_with_empty_output = {"retcode": 0, "stdout": all_the_whitespaces}
        mock_runall = MagicMock(return_value=success_with_empty_output)
        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            result = flatpak.install(location="fnord_location", name="fnord_name")

            self.assertTrue(result["result"])
            self.assertEqual(result["stdout"], "")

    def test_is_installed_should_use_the_correct_flatpak_command(self):
        ...

    def test_is_installed_should_be_False_when_flatpak_returns_nonzero_and_stderr(self):
        ...

    def test_is_installed_should_be_True_when_flatpak_returns_zero_and_stderr(self):
        ...

    def test_is_installed_should_be_True_when_flatpak_returns_zero(self):
        ...

    def test_uninstall_uses_correct_flatpak_command(self):
        import pytest

        pytest.skip()
        expected_command = "NOT_REALLY_FLATPAK uninstall fnord_location fnord_name"

        mock_runall = MagicMock()
        patch_flatpak_binary = patch(
            "salt.modules.flatpak.FLATPAK_BINARY_NAME", "NOT_REALLY_FLATPAK"
        )
        patch_runall = patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall})
        with patch_flatpak_binary, patch_runall:
            # flatpak.uninstall(location="fnord_location", name="fnord_name")
            command = mock_runall.call_args.args[0]
            self.assertEqual(command, expected_command)

    def test_uninstall_should_fail_when_flatpak_returns_nonzero_and_stderr(self):
        import pytest

        pytest.skip()
        # Based on flapak code as of 2020-04-30 when there's an error
        # running flatpak it will return both nonzero and dump to stderr.
        # If this changes in the future, this test will need to be modified.
        # arrange
        expected_stderr = "fnord"
        error_result = {"retcode": 1, "stderr": expected_stderr}
        mock_runall = MagicMock(return_value=error_result)

        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            # act
            # result = flatpak.uninstall(location='fnord_location', name='fnord_name')

            # assert
            # self.assertFalse(result["result"])
            # self.assertEqual(result["stderr"], expected_stderr)
            ...

    def test_uninstall_should_not_fail_when_flatpak_returns_zero_and_stderr(self):
        import pytest

        pytest.skip()
        expected_stdout = "some fnordy stdout"
        success_with_stderr = {
            "retcode": 0,
            "stderr": "some fnordy stderr",
            "stdout": expected_stdout,
        }
        mock_runall = MagicMock(return_value=success_with_stderr)
        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            # result = flatpak.uninstall(location='fnord_location', name='fnord_name')

            # self.assertTrue(result["result"])
            # self.assertEqual(result["stdout"], expected_stdout)
            ...

    def test_uninstall_should_succed_when_flatpak_returns_zero_with_output(self):
        import pytest

        pytest.skip()
        expected_stdout = "This is a fnordy stdout. There is something here."
        success_with_empty_output = {"retcode": 0, "stdout": expected_stdout}
        mock_runall = MagicMock(return_value=success_with_empty_output)
        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            # result = flatpak.uninstall(location='fnord_location', name='fnord_name')

            # self.assertTrue(result["result"])
            # self.assertEqual(result["stdout"], expected_stdout)
            ...

    def test_uninstall_should_succed_with_only_whitespace_output(self):
        import pytest

        pytest.skip()
        expected_stdout = ""
        all_the_whitespaces = "\n\t\t\n\f     "
        success_with_empty_output = {"retcode": 0, "stdout": all_the_whitespaces}
        mock_runall = MagicMock(return_value=success_with_empty_output)
        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            # result = flatpak.uninstall(location='fnord_location', name='fnord_name')

            # self.assertTrue(result["result"])
            # self.assertEqual(result["stdout"], "")
            ...

    def test_add_remote_uses_correct_flatpak_command(self):
        import pytest

        pytest.skip()
        expected_command = "NOT_REALLY_FLATPAK add_remote fnord_location fnord_name"

        mock_runall = MagicMock()
        patch_flatpak_binary = patch(
            "salt.modules.flatpak.FLATPAK_BINARY_NAME", "NOT_REALLY_FLATPAK"
        )
        patch_runall = patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall})
        with patch_flatpak_binary, patch_runall:
            flatpak.add_remote(location="fnord_location", name="fnord_name")
            command = mock_runall.call_args.args[0]
            self.assertEqual(command, expected_command)

    def test_add_remote_should_fail_when_flatpak_returns_nonzero_and_stderr(self):
        import pytest

        pytest.skip()
        # Based on flapak code as of 2020-04-30 when there's an error
        # running flatpak it will return both nonzero and dump to stderr.
        # If this changes in the future, this test will need to be modified.
        # arrange
        expected_stderr = "fnord"
        error_result = {"retcode": 1, "stderr": expected_stderr}
        mock_runall = MagicMock(return_value=error_result)

        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            # act
            result = flatpak.add_remote(location="fnord_location", name="fnord_name")

            # assert
            self.assertFalse(result["result"])
            self.assertEqual(result["stderr"], expected_stderr)

    def test_add_remote_should_not_fail_when_flatpak_returns_zero_and_stderr(self):
        import pytest

        pytest.skip()
        expected_stdout = "some fnordy stdout"
        success_with_stderr = {
            "retcode": 0,
            "stderr": "some fnordy stderr",
            "stdout": expected_stdout,
        }
        mock_runall = MagicMock(return_value=success_with_stderr)
        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            result = flatpak.add_remote(location="fnord_location", name="fnord_name")

            self.assertTrue(result["result"])
            self.assertEqual(result["stdout"], expected_stdout)

    def test_add_remote_should_succed_when_flatpak_returns_zero_with_output(self):
        import pytest

        pytest.skip()
        expected_stdout = "This is a fnordy stdout. There is something here."
        success_with_empty_output = {"retcode": 0, "stdout": expected_stdout}
        mock_runall = MagicMock(return_value=success_with_empty_output)
        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            result = flatpak.add_remote(location="fnord_location", name="fnord_name")

            self.assertTrue(result["result"])
            self.assertEqual(result["stdout"], expected_stdout)

    def test_add_remote_should_succed_with_only_whitespace_output(self):
        import pytest

        pytest.skip()
        expected_stdout = ""
        all_the_whitespaces = "\n\t\t\n\f     "
        success_with_empty_output = {"retcode": 0, "stdout": all_the_whitespaces}
        mock_runall = MagicMock(return_value=success_with_empty_output)
        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            result = flatpak.add_remote(location="fnord_location", name="fnord_name")

            self.assertTrue(result["result"])
            self.assertEqual(result["stdout"], "")

    def test_is_remote_added_should_use_the_correct_flatpak_command(self):
        expected_command = "NOT_REALLY_SOME_OTHER_FLATPAK remotes"

        mock_runall = MagicMock()
        patch_flatpak_binary = patch(
            "salt.modules.flatpak.FLATPAK_BINARY_NAME", "NOT_REALLY_SOME_OTHER_FLATPAK"
        )
        patch_runall = patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall})
        with patch_flatpak_binary, patch_runall:
            flatpak.is_remote_added(remote="fnord")
            command = mock_runall.call_args.args[0]
            self.assertEqual(command, expected_command)

    def test_is_remote_added_with_no_remotes_should_return_False(self):
        no_remotes_output = {"retcode": 0, "stdout": "", "stderr": ""}
        mock_runall = MagicMock(return_value=no_remotes_output)
        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            result = flatpak.is_remote_added(remote="fnord")

            self.assertFalse(result)

    def test_is_remote_added_with_results_not_including_remote_should_return_False(
        self,
    ):
        remote_output = textwrap.dedent(
            """
            \t\t\twhatever\t\there are some\tthings
            \t\t\tdoesn't really matter
            it's not here
            """
        )
        target = "fnord"
        remotes_excluding_target_output = {
            "retcode": 0,
            "stdout": remote_output,
            "stderr": "",
        }
        mock_runall = MagicMock(return_value=remotes_excluding_target_output)
        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            result = flatpak.is_remote_added(remote=target)

            self.assertFalse(result)

    def test_is_remote_added_with_results_should_return_False_if_target_in_output_but_wrong_field(
        self,
    ):
        remote_output = textwrap.dedent(
            """
            \t\tno\tfnord\there\t\t
            really\tfnord\nno\tfnord
            x\t\t\t\t\t\t\t\tfnord fnord fnord\tfnord\tfnord
            fnordy\t\t\t\tfnord fnord\t\t\fhello\tfnord
            testrepo\tTest Repository\thttp://209.132.179.91/repo/\tno-gpg-verify
            """
        )
        target = "fnord"
        remotes_excluding_target_output = {
            "retcode": 0,
            "stdout": remote_output,
            "stderr": "",
        }
        mock_runall = MagicMock(return_value=remotes_excluding_target_output)
        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            result = flatpak.is_remote_added(remote=target)

            self.assertFalse(result)

    def test_is_remote_added_with_results_that_include_target_remote_should_return_True(
        self,
    ):
        remote_output = textwrap.dedent(
            """
            \t\tfoo\tbar fnord funtimes
            fnord\tThis is really a fnord thing
            """
        )
        target = "fnord"
        remotes_including_target_output = {
            "retcode": 0,
            "stdout": remote_output,
            "stderr": "",
        }
        mock_runall = MagicMock(return_value=remotes_including_target_output)
        with patch.dict(flatpak.__salt__, {"cmd.run_all": mock_runall}):
            result = flatpak.is_remote_added(remote=target)

            self.assertTrue(result)
