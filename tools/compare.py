import yaml

def load_yaml(file_path):
    """Loads a YAML file and returns its content as a dictionary."""
    with open(file_path, 'r') as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as e:
            print(f"Error reading YAML file {file_path}: {e}")
            return None

def get_all_keys(data, parent_key=''):
    """
    Recursively retrieves all keys from the YAML structure.
    Supports nested fields by concatenating parent and child keys.
    """
    keys = []
    for key, value in data.items():
        full_key = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value, dict):
            keys.extend(get_all_keys(value, full_key))
        else:
            keys.append(full_key)
    return keys

def compare_yaml_fields(file1_path, file2_path):
    """Compares the fields (keys) of two YAML files, including nested fields."""
    # Load both YAML files
    yaml1 = load_yaml(file1_path)
    yaml2 = load_yaml(file2_path)

    if yaml1 is None or yaml2 is None:
        print("Error in loading YAML files. Exiting comparison.")
        return False

    # Get all keys (including nested) from both YAML files
    keys1 = set(get_all_keys(yaml1))
    keys2 = set(get_all_keys(yaml2))

    if keys1 == keys2:
        print("Both YAML files have the same fields.")
        return True
    else:
        print("YAML files have different fields.")
        
        # Fields that are in file1 but not in file2
        diff1 = keys1 - keys2
        if diff1:
            print(f"Fields in {file1_path} but not in {file2_path}:")
            for key in diff1:
                print(f"  - {key}")

        # Fields that are in file2 but not in file1
        diff2 = keys2 - keys1
        if diff2:
            print(f"Fields in {file2_path} but not in {file1_path}:")
            for key in diff2:
                print(f"  - {key}")
        
        return False


# Example usage:
file1_path = "file.yaml"
file2_path = "file2.yaml"
compare_yaml_fields(file1_path, file2_path)
