# Use Python 3.12 slim image as the base
FROM python:3.12-slim-bookworm

# Set environment variables
ENV HELM_VERSION=v3.13.1
ENV KUBECTL_VERSION=v1.28.0

# Install necessary tools and Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        tar \
        gzip \
        python3-venv \
        python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install Helm
RUN curl -L https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz | \
    tar -xz -C /tmp && \
    mv /tmp/linux-amd64/helm /usr/local/bin/helm && \
    rm -rf /tmp/linux-amd64

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/kubectl

# Create a user with UID 999
RUN useradd -ms /bin/bash -u 999 helmuser

# Copy your Helm plugin into the image
COPY . /quix-manager/

# Set working directory
WORKDIR /quix-manager

# Set ownership of /quix-manager to user 999
RUN chown -R 999:999 /quix-manager

# Switch to user 999
USER 999

# Install the Helm plugin as user 999
RUN helm plugin install /quix-manager

# Set the default command
CMD ["helm"]
