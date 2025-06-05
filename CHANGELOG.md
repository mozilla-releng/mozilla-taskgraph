## 3.2.0 (2025-06-03)

### Added

- landoscript payload builder (#98)

## 3.1.2 (2025-05-22)

### Fix

- add missing mac signed_artifacts

## 3.1.1 (2025-05-22)

### Fix

- stop adding format scopes in scriptworker-signing payload builder

## 3.1.0 (2025-04-25)

### Feat

- add a scriptworker-signing payload builder

## 3.0.4 (2025-04-11)

### Fix

- support Taskgraph 14

## 3.0.3 (2025-02-14)

### Fix

- Fix the previous release so it points to a commit on main

## 3.0.2 (2025-02-14)

### Fix

- Support taskgraph 13

## 3.0.1 (2024-10-25)

### Fix

- declare support for Taskgraph 12.x

## 3.0.0 (2024-10-08)

### BREAKING CHANGE

- Drops support for Taskgraph <11

### Feat

- support Taskgraph >11, <12
- use 'scriptworker.scope-prefix' config for mark-as-shipped

## 2.0.3 (2024-06-21)

### Fix

- declare support for Taskgraph 9.x

## 2.0.2 (2024-05-09)

### Fix

- **bitrise**: Properly handle bitrise payloads to allow permutations of same workflow

## 2.0.1 (2024-05-08)

### Feat

- **bitrise**: Add commit_message and pull_request_id to bitrise payloads

### Fix

- **version**: Fix version to 2.0.1

## 2.0.0 (2024-05-08)

### Feat

- **bitrisescript**: Add global and workflow params

## 1.5.0 (2024-04-11)

### Feat

- **bitrise**: support new 'artifact_prefix' task config

## 1.4.1 (2024-04-09)

### Fix

- declare support for Taskgraph 8.x

## 1.4.0 (2024-04-05)

### Feat

- **bitrise**: support an easier format for environment variables
- **bitrise**: support an easier format for environment variables

## 1.3.2 (2024-04-02)

### Fix

- **bitrise**: normalize refs in bitrise payload builder

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
