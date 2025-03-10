import unittest
from src.helm_manager import FileManager
import os
import tarfile
import tempfile
import unittest
import yaml

class TestFileManager(unittest.TestCase):

    def test_create_folder(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Create a new subfolder path that does not exist yet.
            folder_path = os.path.join(tmpdirname, "new_folder")
            self.assertFalse(os.path.exists(folder_path))
            FileManager.create_folder(folder_path)
            self.assertTrue(os.path.exists(folder_path))
            self.assertTrue(os.path.isdir(folder_path))

    def test_delete_folder(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Create a folder that we will delete.
            folder_path = os.path.join(tmpdirname, "folder_to_delete")
            os.makedirs(folder_path)
            self.assertTrue(os.path.exists(folder_path))
            FileManager.delete_folder(folder_path)
            self.assertFalse(os.path.exists(folder_path))

    def test_extract_tgz(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Create a temporary file to include in the archive.
            file_name = "test.txt"
            file_content = "Hello, World!"
            file_path = os.path.join(tmpdirname, file_name)
            with open(file_path, "w") as f:
                f.write(file_content)
            
            # Create a .tgz archive containing the file.
            archive_path = os.path.join(tmpdirname, "archive.tgz")
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(file_path, arcname=file_name)
            
            # Create an extraction directory.
            extract_dir = os.path.join(tmpdirname, "extracted")
            os.makedirs(extract_dir)
            
            # Extract the archive.
            FileManager.extract_tgz(archive_path, extract_dir)
            
            # Verify that the file exists and its content is correct.
            extracted_file_path = os.path.join(extract_dir, file_name)
            self.assertTrue(os.path.exists(extracted_file_path))
            with open(extracted_file_path, "r") as f:
                content = f.read()
            self.assertEqual(content, file_content)

    def test_copy_and_rename(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Create a source file.
            src_file = os.path.join(tmpdirname, "source.txt")
            content = "Sample content for copy."
            with open(src_file, "w") as f:
                f.write(content)
            
            # Define the destination file path.
            dest_file = os.path.join(tmpdirname, "copied.txt")
            
            # Copy and rename the file.
            FileManager.copy_and_rename(src_file, dest_file)
            self.assertTrue(os.path.exists(dest_file))
            with open(dest_file, "r") as f:
                copied_content = f.read()
            self.assertEqual(copied_content, content)
            
            # Test behavior when source file does not exist.
            non_existent = os.path.join(tmpdirname, "non_existent.txt")
            with self.assertLogs(level="ERROR") as log:
                FileManager.copy_and_rename(non_existent, dest_file)
            self.assertTrue(any("File not found" in message for message in log.output))

    def test_write_values_string(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            file_path = os.path.join(tmpdirname, "test.txt")
            value = "This is a test string."
            FileManager.write_values(file_path, value)
            with open(file_path, "r") as f:
                content = f.read()
            self.assertEqual(content, value)

    def test_write_values_dict(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            file_path = os.path.join(tmpdirname, "test.yaml")
            data = {"key1": "value1", "key2": 2, "list": [1, 2, 3]}
            FileManager.write_values(file_path, data)
            with open(file_path, "r") as f:
                loaded = yaml.safe_load(f)
            self.assertEqual(loaded, data)
if __name__ == '__main__':
    unittest.main()
