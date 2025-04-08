# Variables
IMAGE_NAME = quixpublic.azurecr.io/helm-quix-install:argocdv2
CONTAINER_NAME = helm-quix-install-container
DOCKER_FILE = Dockerfile
# By default, we'll build for both amd64 and arm64; you can customize as needed
PLATFORM ?= linux/amd64,linux/arm64

# Build the Docker image for the local architecture (no multi-arch)
build:
	@echo "Building Docker image for the local architecture..."
	docker build -t $(IMAGE_NAME) -f $(DOCKER_FILE) .

# Build a multi-arch image (via Buildx) without pushing
build-multiarch:
	@echo "Building multi-architecture Docker image..."
	docker buildx build \
		--platform $(PLATFORM) \
		-t $(IMAGE_NAME) \
		-f $(DOCKER_FILE) \
		. 

# Run the Docker container
run:
	@echo "Running Docker container..."
	docker run --rm --name $(CONTAINER_NAME) \
		$(IMAGE_NAME)

# Publish multi-arch images to the registry
publish:
	@echo "Publishing multi-arch container to registry..."
	docker buildx build \
		--platform $(PLATFORM) \
		--push \
		-f $(DOCKER_FILE) \
		-t $(IMAGE_NAME) \
		.

# Clean up Docker images and containers
clean:
	@echo "Cleaning up Docker images and containers..."
	docker rm -f $(CONTAINER_NAME) || true
	docker rmi -f $(IMAGE_NAME) || true

# Rebuild and run the container locally
rebuild: clean build run

.PHONY: build build-multiarch run clean rebuild publish
