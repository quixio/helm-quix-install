# helm-install-env-var 

## Installing

Requirements
- python 3.8+
- git
- helm
- jinja2

**Run in your favorite terminal (Run as Administrator in Windows)**
```
helm plugin install http://github.com/joseenrique/helm-install-env-var
```

## Usage
- Be sure to have added your dependent charts according to this guide: https://docs.helm.sh/helm/#helm-dependency
- Navigate to the directory that contains your outer values.yaml file to run these commands
  
Command:

```
helm install-env-var --name <namelocalchart> -v <absolute path of values.yaml> -c <absolute path of Charts.yaml>
```

Example:
```
helm  install-env-var --name test -v $(pwd)/test/values.yaml -c $(pwd)/test/Charts.yaml
```
- Open values.yaml, edit and remove things you don't need to override the dependency's default values

## Uninstalling

**Run in your favorite terminal (Run as Administrator in Windows)**
```
helm plugin remove install-env-var
```

## Rendering templates
You can use the environment variables from your system to pass and render to your documents

The syntax:

{{ "default" | ENV('TEST_VAR') }}

```
apiVersion: v2
name: test-fakfa
version: 1.1.0
appVersion: 1.11.12
description: This Chart deploys Kafka.
dependencies:
  - name: kafka
    condition: kafka.enabled
    repository: https://charts.bitnami.com/bitnami
    version: {{ "20.0.2" | ENV('VERSION') }}

```
