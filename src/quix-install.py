import os, argparse, logging
from tools import  HelmManager


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quix Installer Helm Plugin")

    # Add your own script-specific parameters here
    parser.add_argument('action')  
    parser.add_argument('--release-name',  help='Run the Helm command in dry-run mode')
    parser.add_argument('--repo',  help='Run the Helm command in dry-run mode')
    parser.add_argument('--override',  help='Run the Helm command in dry-run mode')
    parser.add_argument('--namespace',  help='Run the Helm command in dry-run mode')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output for this script')

    # Parse known and unknown arguments
    args, helm_args = parser.parse_known_args()

    #print (args)
    # You can handle your custom logic here before running the Helm command

    helm_manager = HelmManager(args)
    helm_manager.update()
    # if args.


