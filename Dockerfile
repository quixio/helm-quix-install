# Use Python 3.12 slim image as the base
FROM python:3.12-slim-bookworm

# Build-time argument for architecture
# docker buildx sets TARGETARCH automatically (e.g. amd64, arm64)
ARG TARGETARCH

# Set environment variables
ENV HELM_VERSION=v3.17.2
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


# Install Helm using $TARGETARCH
# For example, if TARGETARCH=amd64, the URL becomes:
# https://get.helm.sh/helm-v3.17.2-linux-amd64.tar.gz
RUN curl -L "https://get.helm.sh/helm-${HELM_VERSION}-linux-${TARGETARCH}.tar.gz" \
    | tar -xz -C /tmp && \
    mv /tmp/linux-${TARGETARCH}/helm /usr/local/bin/helm && \
    rm -rf /tmp/linux-${TARGETARCH}

# Install kubectl using $TARGETARCH
# For example, if TARGETARCH=amd64, the URL becomes:
# https://dl.k8s.io/release/v1.28.0/bin/linux/amd64/kubectl
RUN curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/kubectl



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
    git \
    python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install Helm using $TARGETARCH
# For example, if TARGETARCH=amd64, the URL becomes:
# https://get.helm.sh/helm-v3.17.2-linux-amd64.tar.gz
RUN curl -L "https://get.helm.sh/helm-${HELM_VERSION}-linux-${TARGETARCH}.tar.gz" \
    | tar -xz -C /tmp && \
    mv /tmp/linux-${TARGETARCH}/helm /usr/local/bin/helm && \
    rm -rf /tmp/linux-${TARGETARCH}

# Install kubectl using $TARGETARCH
# For example, if TARGETARCH=amd64, the URL becomes:
# https://dl.k8s.io/release/v1.28.0/bin/linux/amd64/kubectl
RUN curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/kubectl


# Create a user with UID 999
RUN useradd -ms /bin/bash -u 999 helmuser

# Switch to user 999
USER 999

# Install the Helm plugin as user 999
RUN helm plugin install https://github.com/quixio/helm-quix-install

# Set the default command
CMD ["helm"]
