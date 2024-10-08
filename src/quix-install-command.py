import argparse
from tools import  HelmManager


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quix Installer Helm Plugin")

    # Add your own script-specific parameters here
    parser.add_argument('action', choices = ["update"], help='Specify the Helm action to perform (e.g., install, upgrade, delete)')
    parser.add_argument('--release-name', required=True, help='Specify the release name for the Helm command')
    parser.add_argument('--repo', required=True,help='Specify the Helm chart repository')
    parser.add_argument('--override', help='Override default values for the Helm chart')
    parser.add_argument('--namespace', help='Specify the Kubernetes namespace for the Helm command')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output for this script and the Helm command')
    # Parse known and unknown arguments
    
    args, helm_args = parser.parse_known_args()


    # You can handle your custom logic here before running the Helm command

    helm_manager = HelmManager(args)
    helm_manager.update()



