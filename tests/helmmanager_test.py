import os
import sys
import tempfile
import unittest
from argparse import Namespace
from unittest.mock import MagicMock, patch
from src.helm_manager  import HelmManager

class TestHelmManager(unittest.TestCase):
    def setUp(self):
        # Create a basic Namespace object with default values.
        self.args = Namespace(
            release_name="test",
            namespace="default",
            timeout=None,
            override=None,
            repo=None,
            action="update"
        )
    def test_init_override_invalid(self):
        """Test that providing an invalid override file causes sys.exit."""
        self.args.override = "/non/existent/file.yaml"
        with self.assertRaises(SystemExit):
            HelmManager(self.args)

    def test_init_override_valid(self):
        """Test that a valid override file sets override_path properly."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"dummy")
            tmp.flush()
            self.args.override = tmp.name
            # Patch _get_remote_version so that __init__ does not try to call external helm commands.
            with patch.object(HelmManager, "_get_remote_version", return_value="1.0.0"):
                hm = HelmManager(self.args)
                self.assertEqual(hm.override_path, tmp.name)
        os.unlink(tmp.name)
    
    def test_init_with_repo(self):
        """Test that providing a repo argument correctly sets repo and version."""
        self.args.repo = "myrepo:2.3.4"
        hm = HelmManager(self.args)
        self.assertEqual(hm.repo, "myrepo")
        self.assertEqual(hm.version, "2.3.4")

    def test_init_timeout(self):
        """Test that providing a rimeout is set properly."""
        self.args.timeout = "1m"
        hm = HelmManager(self.args)
        self.assertEqual(hm.timeout, "1m")

    def test_init_no_repo(self):
        """Test that if repo is not provided, _get_remote_version is used and default repo is set."""
        self.args.repo = None
        with patch.object(HelmManager, "_get_remote_version", return_value="9.9.9"):
            hm = HelmManager(self.args)
            self.assertEqual(hm.repo, "quixcontainerregistry.azurecr.io/helm/quixplatform-manager")
            self.assertEqual(hm.version, None)

    def test_extract_version_and_format_valid(self):
        """Test _extract_version_and_format with a valid repository string."""
        self.args.repo = "quixcontainerregistry.azurecr.io/helm/quixplatform-manager:1.2.3"
        hm = HelmManager(self.args)
        repo, version = hm._extract_version_and_format(self.args.repo)
        self.assertEqual(repo, "quixcontainerregistry.azurecr.io/helm/quixplatform-manager")
        self.assertEqual(version, "1.2.3")

    def test_get_values(self):
        """Test _get_values returns the expected helm values output."""
        with patch.object(HelmManager, "_get_remote_version", return_value="1.0.0"):
            hm = HelmManager(self.args)
            dummy_output = b"key: value\nanother: test"
            hm._run_helm_with_args = MagicMock(return_value=MagicMock(stdout=dummy_output))
            values = hm._get_values("test")
            self.assertEqual(values, "key: value\nanother: test")
    
    def test_extract_version_from_stdout(self):
        """Test that _extract_version_from_stdout extracts the version correctly."""
        self.args.repo = "dummy:0.0.1"
        with patch.object(HelmManager, "_get_remote_version", return_value="0.0.1"):
            hm = HelmManager(self.args)
            # Provide an output with at least 9 whitespace‐separated fields.
            helm_output = "a b c d e f g h chart-1.2.3"
            version = hm._extract_version_from_stdout(helm_output)
            self.assertEqual(version, "1.2.3")

    def test_check_remote_chart(self):
        """Test that _check_remote_chart returns helm output without the header."""
        with patch.object(HelmManager, "_get_remote_version", return_value="1.0.0"):
            hm = HelmManager(self.args)
            dummy_output = b"HEADER\nline1\nline2"
            hm._run_helm_with_args = MagicMock(return_value=MagicMock(stdout=dummy_output))
            result = hm._check_remote_chart("test")
            self.assertEqual(result, "line1\nline2")

    def test_get_remote_version(self):
        """Test that _get_remote_version extracts version from helm output."""
        self.args.repo = None
        with patch.object(HelmManager, "_get_remote_version", return_value="2.0.0"):
            hm = HelmManager(self.args)
        # Patch _check_remote_chart and _extract_version_from_stdout to simulate helm output.
        hm._check_remote_chart = MagicMock(return_value="a b c d e f g h chart-2.0.0")
        hm._extract_version_from_stdout = MagicMock(return_value="2.0.0")
        version = hm._get_remote_version("test")
        self.assertEqual(version, "2.0.0")

    def test_check_if_exists(self):
        """Test _check_if_exists returns True if the release name is found in the output."""
        self.args.repo = "dummy:0.0.1"
        hm = HelmManager(self.args)
        hm._check_remote_chart = MagicMock(return_value="some release test content")
        exists = hm._check_if_exists("test")
        self.assertTrue(exists)
        hm._check_remote_chart = MagicMock(return_value="no release info")
        exists = hm._check_if_exists("test")
        self.assertFalse(exists)

    def test_parse_output(self):
        """Test that parse_output converts helm output into a dictionary."""
        output_str = "STATUS: deployed\nREVISION: 2\nOTHER: value"
        result = HelmManager.parse_output(output_str)
        self.assertEqual(result, {"STATUS": "deployed", "REVISION": "2", "OTHER": "value"})


    def test_get_release_status(self):
        """Test that _get_release_status parses helm status output correctly."""
        self.args.repo = "dummy:0.0.1"
        hm = HelmManager(self.args)
        dummy_output = b"STATUS: deployed\nREVISION: 3"
        hm._run_helm_with_args = MagicMock(return_value=MagicMock(stdout=dummy_output))
        status = hm._get_release_status()
        self.assertEqual(status.get("STATUS"), "deployed")
        self.assertEqual(status.get("REVISION"), "3")

    def test_pull_repo(self):
        """Test that pull_repo builds the correct helm command."""
        self.args.repo = "myrepo:2.0.0"
        hm = HelmManager(self.args)
        hm.deployment.get_dir = MagicMock(return_value="/tmp/deployment")
        hm._run_helm_with_args = MagicMock(return_value=MagicMock(stdout=b""))
        hm._pull_repo()
        expected_args = ['pull', 'oci://myrepo', '--version', '2.0.0', '--destination', "/tmp/deployment"]
        hm._run_helm_with_args.assert_called_with(expected_args)
        
    def test_extract_chart(self):
        """Test that extract_chart calls FileManager methods with expected file paths."""
        self.args.repo = "myrepo:2.0.0"
        hm = HelmManager(self.args)
        hm.deployment.get_dir = MagicMock(return_value="/tmp/deployment")
        hm.default_file_path = "/tmp/deployment/testdefault.yaml"
        with patch('src.helm_manager.FileManager.extract_tgz') as mock_extract, \
             patch('src.helm_manager.FileManager.copy_and_rename') as mock_copy:
            hm._extract_chart()
            chart_name = "myrepo"
            expected_archive = os.path.join("/tmp/deployment", f"{chart_name}-2.0.0.tgz")
            expected_values_path = os.path.join("/tmp/deployment", chart_name, "values.yaml")
            mock_extract.assert_called_with(archive=expected_archive, path="/tmp/deployment")
            mock_copy.assert_called_with(from_path=expected_values_path, new_filename="/tmp/deployment/testdefault.yaml")


    def test_run_nonexistent_release(self):
        """
        Test run when the release does not exist and its status is not 'pending-upgrade',
        which should trigger sys.exit(1).
        """
        self.args.repo = "myrepo:2.0.0"
        hm = HelmManager(self.args)
        hm._check_if_exists = MagicMock(return_value=False)
        hm._get_release_status = MagicMock(return_value={"STATUS": "unknown"})
        with self.assertRaises(SystemExit):
            hm.run()



    def test_run_update(self):
        """Test the run method when release exists and action is update."""
        self.args.repo = "myrepo:2.0.0"
        self.args.action = "update"
        hm = HelmManager(self.args)
        # Simulate that the release exists.
        hm._check_if_exists = MagicMock(return_value=True)
        hm._get_values = MagicMock(return_value="dummy values")
        hm._pull_repo = MagicMock()
        hm._extract_chart = MagicMock()
        hm._update_with_merged_values = MagicMock()
        # Patch FileManager.write_values and YamlMerger usage.
        with patch('src.helm_manager.FileManager.write_values') as mock_write, \
             patch('src.helm_manager.YamlMerger') as mock_yaml_merger:
            dummy_yaml_merger = MagicMock()
            dummy_yaml_merger.save_merged_yaml = MagicMock()
            mock_yaml_merger.return_value = dummy_yaml_merger
            hm.run()
            hm._pull_repo.assert_called_once()
            hm._extract_chart.assert_called_once()
            mock_write.assert_called_once()
            dummy_yaml_merger.save_merged_yaml.assert_called_once_with(file_path=hm.merged_file_path)
            hm._update_with_merged_values.assert_called_once()

if __name__ == '__main__':
    unittest.main()
