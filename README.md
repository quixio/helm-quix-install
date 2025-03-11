# Quix Manager - Helm Plugin
## Overview

The quix-manager plugin is a Python-based tool that provides an interface to manage Helm charts for Kubernetes. It supports essential Helm actions like update and template, along with the ability to generate logs and export them as a Kubernetes ConfigMap, ideal for integration with CI/CD systems like ArgoCD. The plugin allows overriding Helm chart values and running Helm commands with enhanced verbosity, ensuring a clear understanding of the execution flow.

## Prerequisites

To use the quix-manager plugin, ensure the following dependencies are installed:

- python 3.9+
- git
- helm

## Installation

Run: 
```
helm plugin install https://github.com/quixio/helm-quix-install
```

## Update the plugin

When you update the plugin, you must update it using the name of it. 

Run: 
```
helm plugin update quix-manager
```


## Usage
This plugin is designed to run via the command line. Below are examples of how to execute the most common Helm actions using `quix-manager`.
  
### Command Structure

```
helm quix-manager <action> --release-name <release-name> --repo <repo-url> [optional-flags]
```

### Supported Actions
- `update`: Updates an existing Helm release.
- `template`: Generates Kubernetes manifest templates without applying them.


### Example Commands

#### Update a Helm Release
To update a release named my-release from a Helm repository located at oci://charts.example.com/helm:latest , run the following command:

```
helm quix-manager update --repo oci://charts.example.com/helm:latest --namespace default
```
- `--repo`: The repository URL for the Helm chart.
- `--namespace`: (Optional) The Kubernetes namespace where the Helm release will be applied. By default the namespace you are set in your context

Also you can update an existing release.
```
helm quix-manager update --override path/file/tooverride
```

This will update  the existing release version with the override file

In addition you could increase the timeout

```
helm quix-manager update --override path/file/tooverride --timeout 10m
```


Ultimately you could re-apply the entire installation in case something went wrong:


```
helm quix-manager update
```


#### Generate Helm Templates
If you want to generate Kubernetes manifest templates without applying them, use the `template` action:

```
helm quix-manager template --repo oci://charts.example.com/helm:latest  --namespace default
```

#### Update Values to Something Custom
If you want to override values in the Helm chart, you can use the `--override` option:

```
helm quix-manager update --repo oci://charts.example.com/helm:latest --override path/file/tooverride
```

The file needs to be in the same format as the values file. The following example represents how to change the deployment service replicacount :

```
platformVariables:
    infrastructure:
        deploymentsService:
            replicaCount: 10
```


#### Verbose Logging
If you need more detailed output, use the `--verbose` flag to enable verbose logging:

```
helm quix-manager update --repo oci://charts.example.com/helm:latest --verbose
```
#### Logs as Configmap
For CI/CD integration (e.g., ArgoCD), the `--logs-as-config` flag allows you to generate a Kubernetes ConfigMap with the logs from the Helm operation:

```
helm quix-manager update --repo oci://charts.example.com/helm:latest  --logs-as-config
```


## Uninstalling

```
helm plugin uninstall quix-manager
```

