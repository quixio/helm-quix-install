import argparse, logging,io, yaml
from src.helmmanager import  HelmManager



# Function to convert logs into a Kubernetes ConfigMap format
def generate_configmap(logs, configmap_name='quix-manager-log-configmap'):
    configmap = {
        'apiVersion': 'v1',
        'kind': 'ConfigMap',
        'metadata': {
            'name': configmap_name,
        },
        'data': {
            'helm-logs': logs
        }
    }
    return configmap



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quix Installer Helm Plugin")

    # Add your own script-specific parameters here
    parser.add_argument('action', choices = ["update","template"], help='Specify the Helm action to perform (e.g., install, upgrade, delete)')
    parser.add_argument('--release-name', required=True, help='Specify the release name for the Helm command')
    parser.add_argument('--repo', required=True,help='Specify the Helm chart repository')
    parser.add_argument('--override', help='Override default values for the Helm chart')
    parser.add_argument('--namespace', help='Specify the Kubernetes namespace for the Helm command')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output for this script and the Helm command')
    parser.add_argument('--logs-as-config', action='store_true', help='Enable verbose output for this script and the Helm command')
    # Parse known and unknown arguments

    # Set up logging
    log_format = '# %(levelname)s: %(message)s'
    
    # Create an in-memory stream to capture logs
    log_stream = io.StringIO()
    
    # Configure logger for both stdout and in-memory logging
    logger = logging.getLogger('helm_logger')
   # Avoid adding duplicate handlers in case the script runs multiple times


    args, helm_args = parser.parse_known_args()

    
    if not logger.hasHandlers():
        # Handler for logging to stdout
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(console_handler)
        
        # Handler for capturing logs in memory
        memory_handler = logging.StreamHandler(log_stream)
        memory_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(memory_handler)
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.info("Starting Helm command execution")

    # Log some initial info
    helm_manager = HelmManager(args)
    helm_manager.run()
    if args.logs_as_config:
        # Retrieve the logs f rom the in-memory log stream
        log_contents = log_stream.getvalue()
    
        # Generate ConfigMap with the captured logs
        configmap_data = generate_configmap(log_contents)
        print(yaml.dump(configmap_data, default_flow_style=False))



