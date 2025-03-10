import unittest
from unittest.mock import MagicMock
from src.helm_manager import DeploymentManager

class TestDeploymentManager(unittest.TestCase):
    def setUp(self):
        self.tempdir = "./tmp_test"
        self.deployment_manager = DeploymentManager(tempdir=self.tempdir)
    
    def test_get_dir(self):
        # Act
        directory = self.deployment_manager.get_dir()
        # Assert
        self.assertEqual(directory, self.tempdir, "get_dir should return the initialized temporary directory")
    
    def test_setup_calls_create_folder_and_returns_true(self):
        # Arrange: Replace file_manager with a mock
        self.deployment_manager.file_manager = MagicMock()
        
        # Act
        result = self.deployment_manager.setup()
        
        # Assert: Verify that create_folder was called with the correct directory
        self.deployment_manager.file_manager.create_folder.assert_called_once_with(self.tempdir)
        self.assertTrue(result, "setup should return True after creating the folder")

if __name__ == '__main__':
    unittest.main()
