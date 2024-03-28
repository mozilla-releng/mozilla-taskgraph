## 1.3.1 (2024-03-28)

### Fix

- Move bitrise build parameters under a 'build_params' namespace

## 1.3.0 (2024-03-22)

### Feat

- **relpro**: allow passing "version" in release-promotion input
- create a bitrisescript payload builder
- Add dummy release promotion task to allow this repository to be used to verify upcoming changes to Ship It & scopes

### Fix

- look for version.txt in cwd, not where mozilla-taskgraph is installed

## 1.2.2 (2024-01-24)

### Fix

- **relpro**: set 'version' parameter

## 1.2.1 (2024-01-18)

### Fix

- **shipit**: make 'shipit.product' optional in graph_config schema

## 1.2.0 (2024-01-16)

### Feat

- **shipit**: allow 'mark-as-shipped' to define product in task

### Fix

- **shipit**: use task name instead of 'mark-as-shipped' as default label

## 1.1.1 (2024-01-04)

### Fix

- **release_promotion**: add missing build_number parameter

## 1.1.0 (2023-12-20)

### Feat

- add a 'release-promotion' action

## 1.0.2 (2023-12-08)

### Fix

- upgrade to Taskgraph 7.0.0

## 1.0.1 (2023-09-19)

### Fix

- mark compatible with Taskgraph 6.x

## 1.0.0 (2023-07-28)

### Feat

- **shipit**: add shipit mark_as_shipped transforms and worker-type

## 0.1.1 (2023-06-21)

### Fix

- add missing __init__.py files

## 0.1.0 (2023-06-21)

### Feat

- add 'release_artifacts' transforms
- create initial scaffolding for mozilla-taskgraph

### Fix

- use proper module name in setup.py
