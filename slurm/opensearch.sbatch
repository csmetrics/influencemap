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
# Why a chain of jobs: the CPU partition caps one job at 7 days, so a
# 3-month service is ~13 back-to-back jobs. Each job resubmits its
# successor when OpenSearch exits (normally: Slurm's TERM 3 min before
# the time limit), until CHAIN_UNTIL (default: 90 days after the first
# submission). The gap between jobs is the queue wait plus container
# start, ~1-2 min when dijkstra is free; the webapp's opensearch-tunnel
# sidecar reconnects by itself. The successor is submitted from the
# ORIGINAL script path (scontrol Command=), so editing this file takes
# effect at the next hand-over.
#
# First submission (on cray, from the repo checkout):
#   mkdir -p /data5/slurm/$USER/data/opensearch/logs
#   sbatch slurm/opensearch.sbatch
#     # or with the pre-Slurm index dir:
#   OS_DATA=/data5/opensearch sbatch slurm/opensearch.sbatch
#
# Optional but recommended — import the image ONCE to a .sqsh so the
# 7-day restarts never depend on Docker Hub being reachable:
#   srun --partition=cpu --nodelist=dijkstra --time=00:30:00 \
#        --cpus-per-task=2 --mem=8G \
#        enroot import -o /data5/slurm/$USER/data/opensearch/opensearch-2.11.1.sqsh \
#        docker://opensearchproject/opensearch:2.11.1
#   (the script picks the .sqsh up automatically when it exists)
#
# Stop for good (kills the running job; a killed job never resubmits):
#   scancel --name=opensearch --user=$USER
# Pause the chain without killing the current job:
#   touch /data5/slurm/$USER/data/opensearch/STOP
#
# Check:
#   squeue --me
#   tail -f /data5/slurm/$USER/data/opensearch/logs/opensearch-<jobid>.out
#   sacct -j <jobid> --format=JobID,State,ReqMem,MaxRSS,Elapsed
#
# Reaching it: OpenSearch binds 127.0.0.1:9201 on dijkstra only (no
# auth, so never a real interface). The webapp's opensearch-tunnel
# forwards through SSH exactly as before. If dijkstra no longer admits
# direct SSH, set OPENSEARCH_SSH_PROXYCMD in the webapp .env to hop via
# cray (see compose.yaml).
#
# Tunables (environment at first submission; propagated to successors):
#   OS_DATA      index directory   (default $OS_ROOT/data)
#   OS_IMAGE     Pyxis image       (default: $OS_ROOT/opensearch-2.11.1.sqsh
#                                   if present, else the docker.io URI)
#   OS_HEAP      JVM heap          (default 8g; keep <= half of --mem)
#   CHAIN_UNTIL  epoch seconds     (default now + 90 days)
#
#SBATCH --job-name=opensearch
#SBATCH --partition=cpu
#SBATCH --nodelist=dijkstra
#SBATCH --time=7-00:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
# TERM to the job step (= the OpenSearch process) 3 min before the
# limit; OpenSearch flushes and exits, then this script resubmits.
#SBATCH --signal=TERM@180
#SBATCH --output=/data5/slurm/%u/data/opensearch/logs/%x-%j.out

set -euo pipefail

OS_ROOT="/data5/slurm/$USER/data/opensearch"
OS_DATA="${OS_DATA:-$OS_ROOT/data}"
OS_HEAP="${OS_HEAP:-8g}"
CHAIN_UNTIL="${CHAIN_UNTIL:-$(( $(date +%s) + 90 * 24 * 3600 ))}"
if [[ -z "${OS_IMAGE:-}" ]]; then
    if [[ -f "$OS_ROOT/opensearch-2.11.1.sqsh" ]]; then
        OS_IMAGE="$OS_ROOT/opensearch-2.11.1.sqsh"
    else
        OS_IMAGE="docker.io#opensearchproject/opensearch:2.11.1"
    fi
fi
# An exit sooner than this means a broken config (bad mount, port in
# use, corrupt index...). Do not chain then, or the job would crash-loop
# for 90 days.
MIN_UPTIME=600

echo "job_id=$SLURM_JOB_ID node=$(hostname) started=$(date -Is)"
echo "image=$OS_IMAGE data=$OS_DATA heap=$OS_HEAP cpus=$SLURM_CPUS_PER_TASK mem=${SLURM_MEM_PER_NODE:-?}M"
echo "chain_until=$(date -Is -d "@$CHAIN_UNTIL")"

if [[ -e "$OS_ROOT/STOP" ]]; then
    echo "STOP file present ($OS_ROOT/STOP) — not starting. Remove it and resubmit."
    exit 0
fi
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
rc=0
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
        /usr/share/opensearch/opensearch-docker-entrypoint.sh opensearch \
    || rc=$?

uptime=$SECONDS
echo "opensearch exited rc=$rc after ${uptime}s at $(date -Is)"

# ---- hand over to the next 7-day job -------------------------------------
if [[ -e "$OS_ROOT/STOP" ]]; then
    echo "STOP file present — chain ends here."
    exit "$rc"
fi
if (( $(date +%s) >= CHAIN_UNTIL )); then
    echo "chain_until reached — chain ends here."
    exit "$rc"
fi
if (( uptime < MIN_UPTIME )); then
    echo "exited after <${MIN_UPTIME}s — assuming broken config, NOT resubmitting."
    exit 1
fi

# Slurm runs a spooled copy of this file, so $0 is useless; resubmit the
# path recorded at submission time.
script=$(scontrol show job "$SLURM_JOB_ID" | sed -n 's/.*Command=\([^ ]*\).*/\1/p')
if [[ ! -f "$script" ]]; then
    echo "cannot find original script ($script) — NOT resubmitting."
    exit 1
fi
# singleton: never two opensearch jobs on the same index at once.
# Drop the parent job's SLURM_* variables so they cannot leak into the
# successor's environment.
next=$(
    unset "${!SLURM_@}" "${!SLURMD_@}"
    sbatch --parsable --dependency=singleton \
        --export=ALL,CHAIN_UNTIL="$CHAIN_UNTIL",OS_DATA="$OS_DATA",OS_IMAGE="$OS_IMAGE",OS_HEAP="$OS_HEAP" \
        "$script"
)
echo "submitted successor job $next"
