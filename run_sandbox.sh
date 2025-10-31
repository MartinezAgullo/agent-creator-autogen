#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="autogen-sandbox:arm64"
CONTAINER_NAME="autogen_sandbox_$(date +%s)"

# Build for Apple Silicon (ARM64)
echo "[INFO] Building image for ARM64..."
docker build --platform linux/arm64 -t "$IMAGE_NAME" .

# Runtime resource limits
MEMORY_LIMIT="2g"
CPUS="2.0"
PIDS_LIMIT="128"

# Ensure local dirs exist
mkdir -p assessments

echo "[INFO] Running sandbox container..."
echo "[INFO] Container name: $CONTAINER_NAME"
echo "[INFO] Memory limit: $MEMORY_LIMIT"
echo "[INFO] CPU limit: $CPUS"

docker run --rm -it \
  --name "$CONTAINER_NAME" \
  --platform linux/arm64 \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=128m,uid=1000,gid=1000 \
  --tmpfs /runtime:rw,exec,nosuid,nodev,size=512m,uid=1000,gid=1000 \
  --tmpfs /home/sandbox:rw,noexec,nosuid,nodev,size=64m,uid=1000,gid=1000 \
  --mount type=bind,source="$(pwd)/assessments",target=/assessments \
  --memory="$MEMORY_LIMIT" \
  --cpus="$CPUS" \
  --pids-limit="$PIDS_LIMIT" \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  --env-file .env \
  -e AGENT_RUNTIME_DIR="/runtime" \
  -e ASSESSMENT_DIR="/assessments" \
  "$IMAGE_NAME" \
  python world.py

echo "[INFO] Sandbox execution completed"