FROM python:3.12-slim-bookworm

# Set environment variables
ENV HELM_VERSION=v3.13.1

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

# Copy your Helm plugin into the image
COPY . /quix-manager/

# Set working directory
WORKDIR /quix-manager


# Install the Helm plugin
RUN helm plugin install ./

# Set the default command
CMD ["helm"]
