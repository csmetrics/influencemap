#!/bin/bash
# OpenSearch as a long-running Slurm job on the CMLab cluster.
# Docs: https://compute.cmlab.dev/docs/  (batch-scripts, containers, resources)
#
# Replaces `docker compose -f compose.opensearch.yaml up` on dijkstra:
# the host is Slurm-managed now, there is no docker group, and
# containers run unprivileged through Enroot/Pyxis (srun
# --container-image). Same image, same settings, same data dir; only
# the launcher changed.
#
# Submit (on cray, from the repo checkout):
#   mkdir -p /data5/slurm/$USER/data/opensearch/logs
#   sbatch slurm/opensearch.sbatch
#     # or with the pre-Slurm index dir:
#   OS_DATA=/data5/opensearch sbatch slurm/opensearch.sbatch
#
# Optional but recommended — import the image ONCE to a .sqsh so a
# restart never depends on Docker Hub being reachable:
#   srun --partition=cpu --nodelist=dijkstra --time=00:30:00 \
#        --cpus-per-task=2 --mem=8G \
#        enroot import -o /data5/slurm/$USER/data/opensearch/opensearch-2.11.1.sqsh \
#        docker://opensearchproject/opensearch:2.11.1
#   (the script picks the .sqsh up automatically when it exists)
#
# Stop:   scancel --name=opensearch --user=$USER
#         (a cancelled job is not requeued; only node failure /
#          maintenance triggers --requeue)
# Check:  squeue --me
#         sacctmgr show qos long-cpu format=Name,MaxWall   # confirm the QOS
#         tail -f /data5/slurm/$USER/data/opensearch/logs/opensearch-<jobid>.out
#         sacct -j <jobid> --format=JobID,State,ReqMem,MaxRSS,Elapsed
#
# Reaching it: OpenSearch binds 127.0.0.1:9201 on dijkstra only (no
# auth, so never a real interface). The webapp's opensearch-tunnel
# forwards through SSH exactly as before. If dijkstra no longer admits
# direct SSH, set OPENSEARCH_SSH_PROXYCMD in the webapp .env to hop via
# cray (see compose.yaml).
#
# Tunables (environment at submission; sbatch exports it by default):
#   OS_DATA      index directory   (default $OS_ROOT/data)
#   OS_IMAGE     Pyxis image       (default: $OS_ROOT/opensearch-2.11.1.sqsh
#                                   if present, else the docker.io URI)
#   OS_HEAP      JVM heap          (default 8g; keep <= half of --mem)
#
#SBATCH --job-name=opensearch
#SBATCH --partition=cpu
#SBATCH --nodelist=dijkstra
# The cpu partition caps ordinary jobs at 7 days; the cluster-wide
# long-cpu QOS raises the ceiling to 731 days (sbatch only, no GPU,
# same priority/fair-share). See compute.cmlab.dev/docs/resources.
#SBATCH --qos=long-cpu
#SBATCH --time=365-00:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
# Come back after a node failure / maintenance reboot. Requeue reruns
# this script from the top on the same job id; the index lives on
# /data5 so there is nothing else to recover. --open-mode=append keeps
# the earlier attempts' output instead of truncating the log.
#SBATCH --requeue
#SBATCH --open-mode=append
# TERM to the job step (= the OpenSearch process) 3 min before the
# limit so it can flush and close the index cleanly instead of being
# KILLed 30 s after the limit.
#SBATCH --signal=TERM@180
#SBATCH --output=/data5/slurm/%u/data/opensearch/logs/%x-%j.out

set -euo pipefail

OS_ROOT="/data5/slurm/$USER/data/opensearch"
OS_DATA="${OS_DATA:-$OS_ROOT/data}"
OS_HEAP="${OS_HEAP:-8g}"
if [[ -z "${OS_IMAGE:-}" ]]; then
    if [[ -f "$OS_ROOT/opensearch-2.11.1.sqsh" ]]; then
        OS_IMAGE="$OS_ROOT/opensearch-2.11.1.sqsh"
    else
        OS_IMAGE="docker.io#opensearchproject/opensearch:2.11.1"
    fi
fi

echo "job_id=$SLURM_JOB_ID node=$(hostname) started=$(date -Is)"
echo "image=$OS_IMAGE data=$OS_DATA heap=$OS_HEAP cpus=$SLURM_CPUS_PER_TASK mem=${SLURM_MEM_PER_NODE:-?}M"

mkdir -p "$OS_DATA"

# vm.max_map_count is a host sysctl we cannot raise here; fall back to
# niofs when it is too low (same OPENSEARCH_ALLOW_MMAP switch compose had).
allow_mmap=true
if (( $(cat /proc/sys/vm/max_map_count) < 262144 )); then
    echo "vm.max_map_count < 262144 -> node.store.allow_mmap=false"
    allow_mmap=false
fi
ulimit -n 65536 2>/dev/null || echo "warning: could not raise nofile, now $(ulimit -n)"

# Environment variables with a dot become -E settings via the image's
# entrypoint — the same mechanism compose.opensearch.yaml relied on.
# bash cannot export such names, hence env(1).
#   --no-container-remap-root  OpenSearch refuses to run as uid 0
#   --no-container-entrypoint  invoke the entrypoint ourselves so its
#                              behaviour does not depend on the Pyxis default
#   --container-writable       the entrypoint removes the security plugin
#                              from the rootfs on start
env \
    discovery.type=single-node \
    network.host=127.0.0.1 \
    http.port=9201 \
    transport.port=9301 \
    node.store.allow_mmap="$allow_mmap" \
    cluster.routing.allocation.disk.watermark.low=95% \
    cluster.routing.allocation.disk.watermark.high=97% \
    cluster.routing.allocation.disk.watermark.flood_stage=98% \
    DISABLE_SECURITY_PLUGIN=true \
    DISABLE_INSTALL_DEMO_CONFIG=true \
    OPENSEARCH_JAVA_OPTS="-Xms$OS_HEAP -Xmx$OS_HEAP" \
    srun --ntasks=1 --cpus-per-task="$SLURM_CPUS_PER_TASK" \
        --container-image="$OS_IMAGE" \
        --container-mounts="$OS_DATA:/usr/share/opensearch/data" \
        --container-workdir=/usr/share/opensearch \
        --container-writable \
        --no-container-remap-root \
        --no-container-entrypoint \
        /usr/share/opensearch/opensearch-docker-entrypoint.sh opensearch

echo "opensearch exited after ${SECONDS}s at $(date -Is)"
