#!/bin/bash
set -e

# Configuration
IMAGE_NAME="grid-surfer"
CONTAINER_NAME="grid-surfer-app"
PORT="${PORT:-8501}"
# Get version from git or use latest
VERSION=$(git describe --always 2>/dev/null || echo "latest")
TAG="${1:-${VERSION}}"

echo "Deploying Grid Surfer application..."

# Stop and remove existing container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping existing container..."
    docker stop "${CONTAINER_NAME}" || true
    docker rm "${CONTAINER_NAME}" || true
fi

# Build the image
echo "Building Docker image..."
./build-docker.sh "${TAG}"

# Run the container
echo "Starting container on port ${PORT}..."
docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${PORT}:8501" \
    --restart unless-stopped \
    "${IMAGE_NAME}:${TAG}"

echo "✅ Grid Surfer deployed successfully!"
echo ""
echo "Application is running at: http://localhost:${PORT}"
echo ""
echo "Container management:"
echo "  View logs: docker logs ${CONTAINER_NAME}"
echo "  Stop:      docker stop ${CONTAINER_NAME}"
echo "  Start:     docker start ${CONTAINER_NAME}"
echo "  Remove:    docker rm ${CONTAINER_NAME}"
