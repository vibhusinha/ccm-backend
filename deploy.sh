#!/bin/bash
set -euo pipefail

# Deploy script for CCM backend microservices on EC2
# Usage: ./deploy.sh <service_name> <ecr_registry> <image_tag>
# Example: ./deploy.sh auth 418884736370.dkr.ecr.eu-west-2.amazonaws.com latest

SERVICE_NAME="${1:?Usage: ./deploy.sh <service> <ecr_registry> <tag>}"
ECR_REGISTRY="${2:?Usage: ./deploy.sh <service> <ecr_registry> <tag>}"
IMAGE_TAG="${3:-latest}"

# Port mapping
declare -A PORTS=(
    [auth]=8001
    [clubs]=8002
    [matches]=8003
    [scoring]=8004
    [communication]=8005
    [commerce]=8006
)

PORT="${PORTS[$SERVICE_NAME]:?Unknown service: $SERVICE_NAME}"
IMAGE="${ECR_REGISTRY}/ccm-${SERVICE_NAME}:${IMAGE_TAG}"
CONTAINER_NAME="ccm-${SERVICE_NAME}"

echo "Deploying ${SERVICE_NAME} service..."
echo "  Image: ${IMAGE}"
echo "  Port:  ${PORT}:8000"

# Pull the latest image
docker pull "${IMAGE}"

# Stop and remove old container (if exists)
docker stop "${CONTAINER_NAME}" 2>/dev/null || true
docker rm "${CONTAINER_NAME}" 2>/dev/null || true

# Start the new container
docker run -d \
    --name "${CONTAINER_NAME}" \
    --restart unless-stopped \
    -p "${PORT}:8000" \
    --env-file /opt/ccm/.env \
    "${IMAGE}"

echo "Deployed ${SERVICE_NAME} service on port ${PORT}"

# Wait for health check
echo "Waiting for health check..."
for i in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:${PORT}/api/v1/health" > /dev/null 2>&1; then
        echo "Health check passed!"
        exit 0
    fi
    sleep 2
done

echo "WARNING: Health check failed after 60s"
docker logs --tail 20 "${CONTAINER_NAME}"
exit 1
