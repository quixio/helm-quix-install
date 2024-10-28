# Quix Manager - Helm Plugin
## Overview

The quix-manager plugin is a Python-based tool that provides an interface to manage Helm charts for Kubernetes. It supports essential Helm actions like update and template, along with the ability to generate logs and export them as a Kubernetes ConfigMap, ideal for integration with CI/CD systems like ArgoCD. The plugin allows overriding Helm chart values and running Helm commands with enhanced verbosity, ensuring a clear understanding of the execution flow.

## Prerequisites

To use the quix-manager plugin, ensure the following dependencies are installed:

- python 3.8+
- git
- helm

## Installation

Run: 
```
helm plugin install https://github.com/quixio/helm-quix-install
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

#### Generate Helm Templates
If you want to generate Kubernetes manifest templates without applying them, use the `template` action:

```
helm quix-manager template --repo oci://charts.example.com/helm:latest  --namespace default
```

#### Override Default Values
If you want to override values in the Helm chart, you can use the `--override` option:

```
helm quix-manager update --repo oci://charts.example.com/helm:latest --override path/file/tooverride
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

