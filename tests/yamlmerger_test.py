import unittest
from unittest.mock import patch, mock_open
import yaml,sys, os

# Add the parent directory of the current file to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.helm_manager import YamlMerger


class TestYamlMerger(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    @patch('yaml.safe_load', return_value={'global': {'version': '1.0'}})
    def test_load_yaml(self, mock_yaml_load, mock_open_file):
        merger = YamlMerger("source.yaml", "new_fields.yaml")
        mock_open_file.assert_any_call("source.yaml", 'r')
        mock_open_file.assert_any_call("new_fields.yaml", 'r')
        self.assertEqual(merger.source_data, {'global': {'version': '1.0'}})

    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    @patch('yaml.safe_load')
    def test_merge_without_override(self, mock_yaml_load, mock_open_file):
        mock_yaml_load.side_effect = [
            {'global': {'version': '1.0'}, 'data': {'field1': 'value1'}},
            {'data': {'field2': 'value2'}, 'global': {'byocZipVersion': '2.0'}, 'image': {'tag': 'latest'}}
        ]
        merger = YamlMerger("source.yaml", "new_fields.yaml")
        merged_data = merger.merge()
        expected_data = {
            'global': {'version': '1.0', 'byocZipVersion': '2.0'},
            'data': {'field1': 'value1', 'field2': 'value2'},
            'image': {'tag': 'latest'}
        }
        self.assertEqual(merged_data, expected_data)

    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    @patch('yaml.safe_load')
    def test_merge_with_override(self, mock_yaml_load, mock_open_file):
        mock_yaml_load.side_effect = [
            {'global': {'version': '1.0','byocZipVersion': '1.0'}, 'data': {'field1': 'value1'}},
            {'data': {'field2': 'value2'}, 'global': {'byocZipVersion': '2.0'}, 'image': {'tag': 'latest'}},
            {'global': {'version': '2.0','byocZipVersion': '2.0'}, 'data': {'field1': 'new_value'}}
        ]
        merger = YamlMerger("source.yaml", "new_fields.yaml", "override.yaml")
        merged_data = merger.merge()
        expected_data = {
            'global': {'version': '2.0', 'byocZipVersion': '2.0'},
            'data': {'field1': 'new_value', 'field2': 'value2'},
            'image': {'tag': 'latest'}
        }
        self.assertEqual(merged_data, expected_data)


    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    def test_merge_new_fields(self, mock_open_file):
        merger = YamlMerger("source.yaml", "new_fields.yaml")
        source = {'key1': 'value1'}
        new_fields = {'key2': 'value2'}
        merged_data = merger._merge_new_fields(source, new_fields)
        self.assertEqual(merged_data, {'key1': 'value1', 'key2': 'value2'})

    @patch('builtins.open', new_callable=mock_open, read_data='{}')
    def test_apply_overrides(self, mock_open_file):
        merger = YamlMerger("source.yaml", "new_fields.yaml")
        data = {'key1': 'value1'}
        overrides = {'key1': 'override_value'}
        overridden_data = merger._apply_overrides(data, overrides)
        self.assertEqual(overridden_data, {'key1': 'override_value'})

if __name__ == '__main__':
    unittest.main()