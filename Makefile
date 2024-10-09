# Variables
IMAGE_NAME=quixpublic.azurecr.io/helm-quix-install:newargo
CONTAINER_NAME=helm-quix-install-container
DOCKER_FILE=Dockerfile
PLATFORM ?= linux/amd64
# Build the Docker image
build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME) -f $(DOCKER_FILE) .

# Run the Docker container
run:
	@echo "Running Docker container..."
	docker run --rm --name $(CONTAINER_NAME) \
		$(IMAGE_NAME)

#Publish to the public registry
publish:
	@echo "Publishing container to ..."
	docker buildx build --platform $(PLATFORM) --push  -f $(DOCKER_FILE) -t $(IMAGE_NAME) .

# Clean up Docker images and containers
clean:
	@echo "Cleaning up Docker images and containers..."
	docker rm -f $(CONTAINER_NAME) || true
	docker rmi -f $(IMAGE_NAME) || true

# Rebuild and run the container
rebuild: clean build run

.PHONY: build run clean rebuild