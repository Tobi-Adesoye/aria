# HDFS NameNode Runbook

service: hdfs-namenode
platform: cdp
cluster: cdp-cluster

## Common errors

- OutOfMemory: NameNode heap exhausted
- ERROR HDFS disk full: DataNode storage exhausted
- FATAL NameNode entering safe mode
- connection refused: NameNode RPC port 8020 unreachable
- timeout connecting to namenode

## Log paths

/var/log/hadoop-hdfs/hadoop-hdfs-namenode.log
/var/log/hadoop-hdfs/hadoop-hdfs-secondarynamenode.log
/var/log/hadoop/hdfs/namenode.log

## Keywords

ERROR WARN FATAL OOM OutOfMemory disk full HDFS NameNode safe mode timeout
