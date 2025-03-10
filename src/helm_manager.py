import os, sys, shutil, subprocess, yaml, tarfile,logging
from argparse import Namespace

logging = logging.getLogger('quix-manager')

class HelmManager:
    def __init__(self, args: Namespace = None):
        """
        Initializes the HelmManager with provided arguments.

        :param args: Parsed command-line arguments for the Helm operation.
        """
        self.release_name = args.release_name if args.release_name else "quixplatform-manager"
        self.namespace = args.namespace or os.environ.get('HELM_NAMESPACE')
        # Validate override file
        if args.override:
            if not os.path.isfile(args.override):
                logging.error(f"Error: The override file '{args.override}' does not exist or is not valid.")
                sys.exit(1)
            else:
                logging.debug(f"Override file found: {args.override}")
                self.override_path = args.override
        else:
            logging.debug("No override file provided.")
            self.override_path = None

        if args.repo:
            self.repo, self.version = self._extract_version_and_format(args.repo)
        else:
            self.version = self._get_remote_version(release_name=self.release_name)
            self.repo = "quixcontainerregistry.azurecr.io/helm/quixplatform-manager"

        self.action = args.action
        # Initialize deployment manager
        self.deployment = DeploymentManager()
        self.deployment.setup()

        deployment_dir = self.deployment.get_dir()
        self.current_file_path = os.path.join(deployment_dir, f"{self.release_name}current.yaml")
        self.default_file_path = os.path.join(deployment_dir, f"{self.release_name}default.yaml")
        self.merged_file_path = os.path.join(deployment_dir, f"{self.release_name}merged.yaml")


    def _run_helm_with_args(self, helm_args: list):
        """
        Runs a Helm command with the provided arguments.

        :param helm_args: List of arguments for the Helm command.
        """
        command = ['helm'] + helm_args
        logging.debug(f"Executing Helm command: {command}")

        try:
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info("Helm command executed successfully.")
            return result
        except subprocess.CalledProcessError as e:
            logging.error(f"Helm command failed: {e.stderr.decode('utf-8')}")
            sys.exit(1)

    def _extract_version_and_format(self, repo):
        """
        Extracts the repository URL and version from the repository string.

        :param repo: The repository string (e.g., 'repo:version').
        :return: Tuple of repository URL and version.
        """
        print (repo)
        try:
            repo_split = repo.split(":")
            return repo_split[0], repo_split[1]
        except (IndexError, ValueError):
            logging.error(f"Invalid repository format: {repo}")
            raise ValueError(f"Invalid version format: {repo}")

    def _get_values(self, release_name: str):
        """
        Retrieves the values of a Helm release.

        :param release_name: Name of the Helm release.
        :return: YAML values of the release.
        """
        list_args = ['get', 'values', release_name]
        if self.namespace:
            list_args.extend(['--namespace', self.namespace])
        return self._run_helm_with_args(list_args).stdout.decode('utf-8')

    def _extract_version_from_stdout(self, helm_output):
        """
        Extracts the chart version from the helm output.

        :param helm_output: Helm output string without header.
        :return: Extracted chart version.
        """
        try:
            parts = helm_output.split()
            if len(parts) < 9:
                raise ValueError(f"Expected at least 9 fields, got {len(parts)}")
            chart_field = parts[8]
            version = chart_field.rsplit("-", 1)[-1]
            logging.debug("Extracted version %s from chart field %s", version, chart_field)
            return version
        except Exception as e:
            logging.error("Error extracting chart version: %s", e)
            raise

    def _check_remote_chart(self, release_name):
        """
        Checks the remote helm chart for the given release.

        :param release_name: Name of the helm release.
        :return: Helm output string without header.
        """
        list_args = ['list', '--filter', release_name]
        if self.namespace:
            list_args.extend(["--namespace", self.namespace])
        try:
            result_obj = self._run_helm_with_args(list_args)
            result = result_obj.stdout.decode('utf-8')
        except Exception as e:
            logging.error("Error running helm command for release %s: %s", release_name, e)
            raise RuntimeError("Helm command execution failed") from e

        try:
            lines = result.splitlines()
            if len(lines) > 1:
                result_without_header = "\n".join(lines[1:])
            else:
                result_without_header = ""
            logging.debug("Helm output without header: %s", result_without_header)
            return result_without_header
        except Exception as e:
            logging.error("Error processing helm output for release %s: %s", release_name, e)
            raise

    def _get_remote_version(self, release_name):
        """
        Gets the remote helm chart version for the specified release.

        :param release_name: Name of the helm release.
        :return: Remote chart version.
        """
        try:
            helm_output = self._check_remote_chart(release_name)
            version = self._extract_version_from_stdout(helm_output)
            logging.info("Retrieved remote version %s for release %s", version, release_name)
            return version
        except Exception as e:
            logging.error("Error retrieving remote version for release %s: %s", release_name, e)
            raise

    def _check_if_exists(self, release_name):
        """
        Checks if a Helm release exists.

        :param release_name: Name of the Helm release.
        :return: True if the release exists, False otherwise.
        """ 
        result = self._check_remote_chart(release_name)
        return (release_name in result)
    
    
    @staticmethod
    def parse_output(output_str):
        """ 
        Parse the output of a Helm command into a dictionary.
        """
        result = {}
        # Split the output into lines and extract key-value pairs
        lines = output_str.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)  
                result[key.strip()] = value.strip()

        return result

    def _rollback(self, revision: str):
        """
        Rollback to the specified revision of a Helm release.
        :param revision: Revision number to rollback to.

        """
        list_args = ['rollback', self.release_name, revision ]
        if self.namespace:
            list_args.extend(['--namespace', self.namespace])
        self._run_helm_with_args(list_args)

        logging.info(f"Rolled back to revision {revision}.")

    def _get_release_status(self):
        """
        Retrieves the current status of a Helm release.

        :param release_name: Name of the Helm release.
        :return: Status of the release.
        """
        list_args = ['status', self.release_name]
        if self.namespace:
            list_args.extend(['--namespace', self.namespace])
        status_result = self._run_helm_with_args(list_args)
        status_output = self.parse_output(status_result.stdout.decode('utf-8'))

        logging.info(f"The status of the Helm chart {self.release_name} is: {status_output.get('STATUS')}")
        return status_output
    
    def _pull_repo(self):
        """
        Pulls the Helm chart from the specified repository.
        """
        try:
            helm_args = ['pull', f"oci://{self.repo}", '--version', self.version, '--destination', self.deployment.get_dir()]
            self._run_helm_with_args(helm_args)
            logging.info(f"Chart {self.repo} pulled successfully.")
        except Exception as e:
            logging.error(f"Error pulling chart: {e}")
            sys.exit(1)

    def _extract_chart(self):
        """
        Extracts the pulled Helm chart from a .tgz file.
        """
        try:
            chart_name = self.repo.split("/")[-1]
            chart_archive = os.path.join(self.deployment.get_dir(), f"{chart_name}-{self.version}.tgz")
            values_path = os.path.join(self.deployment.get_dir(), chart_name, "values.yaml")
            FileManager.extract_tgz(archive=chart_archive, path=self.deployment.get_dir())
            FileManager.copy_and_rename(from_path=values_path, new_filename=self.default_file_path)
            logging.info(f"Chart {chart_name} extracted successfully.")
        except Exception as e:
            logging.error(f"Error extracting chart: {e}")
            sys.exit(1)

    def _update_with_merged_values(self):
        """
        Updates or installs the Helm release with the merged values.
        """
        logging.info("Updating Helm release with merged values.")
        list_args = ['upgrade', '--install', "quixplatform-manager", f"oci://{self.repo}", "--version", self.version, "--values", self.merged_file_path]
        if self.namespace:
            list_args.extend(["--namespace", self.namespace])
        self._run_helm_with_args(list_args)

    def _template_with_merged_values(self):
        """
        Templates the Helm release with the merged values.
        """
        logging.info("Templating Helm release with merged values.")
        list_args = ['template', "quixplatform-manager", f"oci://{self.repo}", "--version", self.version, "--values", self.merged_file_path]
        if self.namespace:
            list_args.extend(["--namespace", self.namespace])
        result = self._run_helm_with_args(list_args)

    def run(self):
        """
        Executes the main logic: checks if the release exists, retrieves values, merges YAML files, 
        and either updates the release or generates a template.
        """

        exist_release = self._check_if_exists(release_name=self.release_name)
        if exist_release:
            try:
                values = self._get_values(release_name=self.release_name)
                self._pull_repo()
                self._extract_chart()
                FileManager.write_values(file_path=self.current_file_path, values=values)
                yaml_merger = YamlMerger(source_file=self.current_file_path, new_fields_file=self.default_file_path, override_file=self.override_path)
                yaml_merger.save_merged_yaml(file_path=self.merged_file_path)
                logging.info("Merged YAML file created.")
                if self.action == "update":
                    self._update_with_merged_values()
                    logging.debug(f"Action {self.action} completed successfully.")
                elif self.action == "template":
                    self._template_with_merged_values()
                    logging.debug(f"Action {self.action} completed successfully.")
                else:
                    #If you use this Class from command line, will not reach cause there is a restriction of choices at the top level
                    logging.error(f"Action {self.action} cannot be used")
                #FileManager.delete_folder(self.deployment.get_dir())
                logging.info(f"{self.action} has been completed successfully.")
            except Exception as e:
                logging.error(f"Error during execution: {e}")
                sys.exit(1)
        else:
            status = self._get_release_status()
            if status.get('STATUS') == 'pending-upgrade':
                logging.debug(f"Release {self.release_name} is in pending-upgrade status.")
                revision = str(int(status.get('REVISION'))-1)
                self._rollback(revision)
                logging.debug(f"Release {self.release_name} has been rolled back and running the upgrade.")
                self.run()
            else:    
                logging.error(f"Release {self.release_name} does not exist. You need to install it first.")
                sys.exit(1)



class FileManager:
    @staticmethod
    def delete_folder(directory: str):
        """
        Deletes the specified directory if it exists.

        :param directory: The path to the directory to be deleted.
        """
        try:
            if os.path.exists(directory):
                shutil.rmtree(directory)
            logging.debug(f"Deleted directory: {directory}")
        except OSError as e:
            logging.error(f"Could not delete the directory {directory}. Error: {str(e)}")

    @staticmethod
    def extract_tgz(archive: str, path: str):
        """
        Extracts a .tgz archive to the specified directory.

        :param archive: The path to the .tgz archive.
        :param path: The path where the archive should be extracted.
        """
        try:
            with tarfile.open(archive, "r:gz") as tar:
                tar.extractall(path, filter=lambda tarinfo, dest: tarinfo)
            logging.debug(f"Extracted archive {archive} to {path}")
        except Exception as e:
            logging.error(f"Error extracting the file {archive}: {e}")
            raise

    @staticmethod
    def create_folder(directory: str):
        """
        Creates the specified directory if it does not exist.

        :param directory: The path to the directory to be created.
        """
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
            logging.debug(f"Created directory: {directory}")
        except OSError as e:
            logging.error(f"Error creating directory {directory}. Error: {str(e)}")

    @staticmethod
    def copy_and_rename(from_path: str, new_filename: str):
        """
        Copies a file from one location to another and renames it.

        :param from_path: The path of the file to be copied.
        :param new_filename: The new name and location of the copied file.
        """
        if os.path.exists(from_path):
            try:
                shutil.copy(from_path, new_filename)
                logging.info(f"Copied and renamed file from {from_path} to {new_filename}")
            except Exception as e:
                logging.error(f"Error copying and renaming file: {e}")
                raise
        else:
            logging.error(f"File not found: {from_path}")

    @staticmethod
    def write_values(file_path: str, values: str):
        """
        Writes YAML or string values to the specified file.

        :param file_path: The path of the file where values will be written.
        :param values: The content to be written to the file, can be a string or a dictionary.
        """
        try:
            with open(file_path, "w") as f:
                if isinstance(values, dict):
                    yaml.dump(values, f, default_flow_style=False, sort_keys=False)
                else:
                    f.write(str(values))
            logging.debug(f"Wrote values to {file_path}")
        except Exception as e:
            logging.error(f"Error writing values to {file_path}: {e}")
            raise



class DeploymentManager:
    def __init__(self, tempdir="./tmp"):
        """
        Initializes the DeploymentManager with a temporary directory.

        :param tempdir: The path to the temporary directory to be used. Default is './tmp'.
        """
        self.tempdir = tempdir
        self.file_manager = FileManager()
        
    def get_dir(self):
        """
        Returns the path to the temporary directory.

        :return: The path of the temporary directory.
        """
        return self.tempdir

    def setup(self):
        """
        Creates the temporary directory using FileManager and logs the action.

        :return: True if the directory is successfully set up.
        """
        self.file_manager.create_folder(self.tempdir)
        return True



class LiteralDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        """
        Increases indentation when dumping YAML content.
        
        :param flow: Determines if the flow style is used (default is False).
        :param indentless: If True, omits indentation (default is False).
        :return: Calls the parent class method to handle indentation.
        """
        return super(LiteralDumper, self).increase_indent(flow, indentless)

def str_presenter(dumper, data):
    """
    Represents multiline strings using the '|' block scalar style in YAML.
    
        - If the string contains newline characters, it uses '|' to preserve newlines.
        - Otherwise, it uses the default string representation.

    :param dumper: The YAML dumper instance.
    :param data: The string data to be represented.
    :return: YAML representation of the string.
    """
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

# Add the custom string presenter to handle multi-line strings in YAML
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
        """
        Loads a YAML file and returns its content as a dictionary.

        :param file_path: The path to the YAML file.
        :return: A dictionary representing the YAML content.
        """
        if file_path:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def merge(self):
        """
        Merges the new fields into the source YAML without overwriting existing fields, 
        and applies the overrides if an override file is provided.

        :return: A dictionary with the merged YAML content.
        """
        # Step 1: Merge new fields into the source without overwriting
        merged_data = self._merge_new_fields(self.source_data, self.new_fields_data)

        # Step 2: Apply overrides if the override file exists
        if self.override_data:
            merged_data = self._apply_overrides(merged_data, self.override_data)

        return merged_data

    def _merge_new_fields(self, source: dict, new_fields: dict):
        """
        Recursively merges new fields into the source without overwriting existing values.

        :param source: The original YAML data.
        :param new_fields: The new fields to add.
        :return: A dictionary with the new fields merged into the source.
        """
        for key, value in new_fields.items():
            if key not in source:
                source[key] = value
            elif isinstance(value, dict) and isinstance(source.get(key), dict):
                # Recursively merge dictionaries
                source[key] = self._merge_new_fields(source[key], value)
        return source

    def _apply_overrides(self, data: dict, overrides: dict):
        """
        Recursively applies override values to the existing data.

        :param data: The original or merged YAML data.
        :param overrides: The override fields to apply.
        :return: A dictionary with the overrides applied.
        """
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
        Saves the merged YAML content to the specified file.

        :param file_path: The file path where the merged YAML will be saved.
        """
        merged_data = self.merge()
        #Special overrides. Always it is more important the new one
        merged_data['global']['byocZipVersion'] = self.new_fields_data['global']['byocZipVersion']
        merged_data['image']['tag'] = self.new_fields_data['image']['tag']
        # Delete User-Supplied Values
        del merged_data['USER-SUPPLIED VALUES']
        FileManager.write_values(file_path=file_path,values=merged_data)