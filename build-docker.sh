#!/bin/bash
set -e

# Configuration
IMAGE_NAME="grid-surfer"
# Get version from git or use unknown
VERSION=$(git describe --always 2>/dev/null || echo "unknown")
TAG="${1:-latest}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

echo "Building Docker image: ${FULL_IMAGE_NAME} (version: ${VERSION})"

# Build the Docker image using buildx with version
docker buildx build --build-arg VERSION="${VERSION}" --tag "${FULL_IMAGE_NAME}" --load .

echo "✅ Docker image built successfully: ${FULL_IMAGE_NAME}"

# Show image info
echo ""
echo "Image details:"
docker images "${IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo ""
echo "To run the container:"
echo "  docker run -p 8501:8501 ${FULL_IMAGE_NAME}"
echo ""
echo "To run in background:"
echo "  docker run -d -p 8501:8501 --name grid-surfer-app ${FULL_IMAGE_NAME}"
