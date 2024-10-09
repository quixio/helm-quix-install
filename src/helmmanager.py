import os, sys, shutil, subprocess, yaml, tarfile,logging
from argparse import Namespace

# log_format = '%(levelname)s: %(message)s' 
# logging.basicConfig(level=logging.DEBUG ,format=log_format)


class HelmManager:
    def __init__(self, args: Namespace = None):
        if args.override:
            if not os.path.isfile(args.override):
                logging.error(f"Error: You use --override and the file '{args.override}' does not exist or is not a valid file.")
                sys.exit(1)
            else:
                self.override_path=args.override
        else:
            self.override_path=None
        self.release_name = args.release_name
        self.repo,self.version = self._extract_version_and_format(args.repo)
        #Statement because it is a globa flag and it is passed by env var
        if not args.namespace:
            args.namespace = os.environ.get('HELM_NAMESPACE')
        self.namespace = args.namespace
        self.action = args.action
        logging.debug(f"Setting namespace as {self.namespace}")
        self.deployment= DeploymentManager()
        self.deployment.setup()
        self.current_file_path=os.path.join(self.deployment.get_dir() ,self.release_name+"current.yaml")
        self.default_file_path=os.path.join(self.deployment.get_dir() ,self.release_name+"default.yaml")
        self.merged_file_path=os.path.join(self.deployment.get_dir() ,self.release_name+"merged.yaml")


    def _run_helm_with_args(self, helm_args: list, output_file: str = None):
        command = ['helm'] + helm_args
        logging.debug(f"Running Helm command: {command}")

        try:
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info("Executed successfully!")
            return result
        except subprocess.CalledProcessError as e:
            logging.error(f"Helm command failed with error: {e.stderr.decode('utf-8')}")
            sys.exit(1)

    def _extract_version_and_format(self,repo):
        try:
            repo_split = repo.split(":")
            return repo_split[0],repo_split[1]
        except (IndexError, ValueError):
            raise ValueError(f"Invalid version format: {self.repo}")

    def _get_values(self, release_name: str):
        list_args = ['get', 'values', release_name]
        if self.namespace:
            list_args.extend(['--namespace', self.namespace])
        return self._run_helm_with_args(list_args).stdout.decode('utf-8')

    def _check_if_exists(self, release_name: str):
        list_args = ['list', '--filter', release_name]
        if self.namespace:
            list_args.extend(["--namespace", self.namespace])
        result = self._run_helm_with_args(list_args)
        if release_name in result.stdout.decode('utf-8'):
            logging.info(f"Exists the release {self.release_name}")
            return True
        logging.info(f"Does not exist the release {self.release_name}")
        return False

    
    def pull_repo(self):
        """Pull the OCI Helm chart from the specified repository."""
        try:
            helm_args = ['pull', f"oci://{self.repo}", '--version', self.version, '--destination', self.deployment.get_dir()]
            self._run_helm_with_args(helm_args)

            logging.info(f"Chart {self.repo} pulled successfully to {self.deployment.get_dir()}.")
        except Exception as e:
            logging.error(f"Error pulling chart: {e}")
            sys.exit(1)

    def extract_chart(self):
        """Extract the pulled chart from the .tgz file."""
        try:
            chart_name = self.repo.split("/")[-1]
            chart_archive = os.path.join(self.deployment.get_dir(), f"{chart_name}-{self.version}.tgz")
            values_path = os.path.join(self.deployment.get_dir(),chart_name ,"values.yaml")
            FileManager.extract_tgz(archive=chart_archive,path=self.deployment.get_dir())
            FileManager.copy_and_rename(from_path=values_path,new_filename=self.default_file_path)
            logging.info(f"Chart extracted to {self.deployment.get_dir()}.")
        except Exception as e:
            logging.error(f"Error extracting chart: {e}")
            sys.exit(1)


    def _update_with_merged_values(self):
        list_args = ['upgrade', '--install', "quixplatform-manager",f"oci://{self.repo}","--version",self.version,"--values",self.merged_file_path]
        if self.namespace:
            list_args.extend(["--namespace", self.namespace])
        #Here template
        self._run_helm_with_args(list_args)

    def _template_with_merged_values(self):
        list_args = ['template', "quixplatform-manager",f"oci://{self.repo}","--version",self.version,"--values",self.merged_file_path]
        if self.namespace:
            list_args.extend(["--namespace", self.namespace])
        #Here template
        result= self._run_helm_with_args(list_args)
        print (result.stdout.decode('utf-8'))

    def run(self):
        exist_release = self._check_if_exists(release_name=self.release_name)
        if exist_release:
            try: 
                values= self._get_values(release_name=self.release_name)
                self.pull_repo()
                self.extract_chart()
                FileManager.write_values(file_path=self.current_file_path,values=values)
                yaml_merger = YamlMerger(source_file=self.current_file_path,new_fields_file=self.default_file_path,override_file=self.override_path)
                yaml_merger.save_merged_yaml(file_path=self.merged_file_path)
                logging.info("Running update...")
                match self.action:
                    case "update":
                        self._update_with_merged_values()
                    case "template":
                        self._template_with_merged_values()
                FileManager.delete_folder(self.deployment.get_dir())
                logging.info("Updated")
            except Exception as e:
                logging.error(f"Something was wrong meanwhile it was doing the merge: Because {e}")
        else:
            logging.info(f"You need to install {self.release_name} first")


class FileManager:
    @staticmethod
    def delete_folder(directory: str):
        try:
            if os.path.exists(directory):
                shutil.rmtree(directory)
            logging.debug(f"Deleted directory: {directory}")
        except OSError as e:
            logging.error(f"Could not delete the directory {directory}. Error: {str(e)}")

    @staticmethod
    def extract_tgz(archive: str, path: str):
        try:
            with tarfile.open(archive, "r:gz") as tar:
                tar.extractall(path)
        except Exception as e:
            logging.error(f"Error extracting the file {archive}: due to {e}")
            raise
    @staticmethod
    def create_folder(directory: str):
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
            logging.debug(f"Created directory: {directory}")
        except OSError as e:
            logging.error(f"Error creating directory {directory}. Error: {str(e)}")

    @staticmethod
    def copy_and_rename(from_path: str,new_filename: str):
        if os.path.exists(from_path):
            try:
                shutil.copy(from_path, new_filename)
                logging.info(f"Copied and renamed values.yaml as {new_filename}")
            except Exception as e:
                logging.error(f"Error copying and renaming values.yaml: {e}")
                raise
        else:
            logging.error(f"No File found")


    @staticmethod
    def write_values(file_path: str, values: str):
        with open(file_path, "w") as f:
            if isinstance(values, dict):
                # If the values are a dictionary, serialize them to YAML format
                yaml.dump(values, f, Dumper=LiteralDumper, default_flow_style=False, sort_keys=False)
            else:
                # Otherwise, treat it as a string and write it directly
                f.write(str(values))
        logging.debug(f"Wrote values to {file_path}")



class DeploymentManager:
    def __init__(self, tempdir="./tmp"):
        self.tempdir = tempdir
        self.file_manager = FileManager()
        
    def get_dir(self):
        return self.tempdir

    def setup(self):
        self.file_manager.create_folder(self.tempdir)
        logging.debug("Created tempdir in {self.tempdir}")
        return True



class LiteralDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(LiteralDumper, self).increase_indent(flow, indentless)

def str_presenter(dumper, data):
    """
    If the string contains newline characters, use the '|' block scalar style.
    This preserves newlines and proper indentation in the output YAML.
    """
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter)

class YamlMerger:
    def __init__(self, source_file: str, new_fields_file: str, override_file: str = None):
        """
        Initializes the class with file paths for the source of truth YAML, the new fields YAML, 
        and an optional override YAML.
        
        :param source_file: The YAML file representing the source of truth.
        :param new_fields_file: The YAML file with potential new fields.
        :param override_file: The YAML file with override fields (optional).
        """
        self.source_file = source_file
        self.new_fields_file = new_fields_file
        self.override_file = override_file

        # Load the YAML files
        self.source_data = self._load_yaml(self.source_file)
        self.new_fields_data = self._load_yaml(self.new_fields_file)
        self.override_data = self._load_yaml(self.override_file) if self.override_file else {}

    def _load_yaml(self, file_path: str):
        """Loads a YAML file and returns its content as a dictionary."""
        if file_path:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def merge(self):
        """
        Merges the new fields into the source of truth without overwriting, 
        and applies the overrides if the override file is provided.
        """
        # Step 1: Merge new fields into the source without overwriting
        merged_data = self._merge_new_fields(self.source_data, self.new_fields_data)

        # Step 2: Apply overrides if the override file exists
        if self.override_data:
            merged_data = self._apply_overrides(merged_data, self.override_data)

        return merged_data

    def _merge_new_fields(self, source: dict, new_fields: dict):
        """Recursively merge new fields into the source without overwriting existing ones."""
        for key, value in new_fields.items():
            if key not in source:
                source[key] = value
            elif isinstance(value, dict) and isinstance(source.get(key), dict):
                # Recursively merge dictionaries
                source[key] = self._merge_new_fields(source[key], value)
        return source

    def _apply_overrides(self, data: dict, overrides: dict):
        """Recursively apply override values to the data."""
        for key, value in overrides.items():
            if isinstance(value, dict) and key in data and isinstance(data[key], dict):
                # Recursively apply overrides if both are dictionaries
                data[key] = self._apply_overrides(data[key], value)
            else:
                # Otherwise, override the value
                data[key] = value
        return data

    def save_merged_yaml(self, file_path: str):
        """
        Saves the merged YAML content to the specified output file.
        
        :param output_file: The file path to save the merged YAML.
        """
        merged_data = self.merge()
        del merged_data['USER-SUPPLIED VALUES']
        FileManager.write_values(file_path=file_path,values=merged_data)