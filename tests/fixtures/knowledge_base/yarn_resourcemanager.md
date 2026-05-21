# YARN ResourceManager Runbook

service: yarn-resourcemanager
platform: cdp
cluster: cdp-cluster

## Common errors

- OutOfMemory: ResourceManager heap too small
- ERROR YARN container allocation failure
- WARN NodeManager lost contact
- connection refused: ResourceManager port 8032
- disk full on NodeManager local dirs

## Log paths

/var/log/hadoop-yarn/yarn-yarn-resourcemanager.log
/var/log/hadoop-yarn/yarn-yarn-nodemanager.log
/var/log/hadoop/yarn/resourcemanager.log

## Keywords

ERROR WARN FATAL OOM OutOfMemory YARN ResourceManager NodeManager container disk full timeout
