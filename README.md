# Homecloud

This repository contains the infrastructure for a personal home cloud built on Kubernetes.

## Overview

The project is designed to provide a robust, automated, and self-hosted cloud environment. It includes a variety of services, from AI chat interfaces to document management and authentication.

## Core Components

- **Kubernetes (`k8s/`)**: The core of the infrastructure, containing all Kubernetes manifests. It uses Kustomize to manage configurations for different services.
- **FluxCD (`k8s/flux-system/`)**: Provides the GitOps capability, automatically syncing the cluster state with the configuration in this repository.
- **CLI (`cli/`)**: A Python-based command-line tool (`hs-cli`) built with Typer for managing the home cloud infrastructure. It simplifies tasks like interacting with Flux, managing secrets with Kubeseal, and handling configurations.
- **Docker Services (`docker/`)**: Contains definitions for custom Docker images used by the services in the cluster.

## Deployed Services

The cluster runs a variety of self-hosted services, including:

### Base Services

- **LibreChat**: An AI chat interface with a vector database and MongoDB backend.
- **Keycloak**: Identity and Access Management solution.
- **Paperless-ngx**: A document management system.
- **Docker Registry**: A private container registry.
- **Photo Upload**: A custom service for photo uploads.
- **Forward Auth & VPN**: Services for authentication and network security.

### Helm-Managed Services

- **Jenkins**: For CI/CD and automation.
- **Longhorn**: Distributed block storage for Kubernetes.
- **Nextcloud**: A suite of client-server software for creating and using file hosting services.
- **Monitoring Stack**: For observing cluster health and performance.
- **GitHub ARC**: GitHub Actions Runner Controller.

## Getting Started

### Prerequisites

- `make`
- `python` & `pip`
- `poetry`
- `kubectl` connected to a Kubernetes cluster

### Installation

To set up the development environment and install the CLI tool, run:

```bash
# Install all development tools and the CLI
make install

# Install only the CLI
make install-cli

# Install pre-commit hooks for code quality
make install-pre-commit
```

## Usage

### CLI Commands

The `hs-cli` tool is the primary way to interact with the cluster for management tasks.

```bash
# Run the CLI from the project root
python cli/main.py

# Example commands:
python cli/main.py flux init          # Initialize FluxCD on the cluster
python cli/main.py flux update-now    # Force an immediate FluxCD reconciliation
python cli/main.py kubeseal           # Encrypt a secret using Kubeseal
python cli/main.py config             # Manage service configurations
```

### Development Workflow (GitOps)

1. **Make Changes**: Modify the service configurations, Kubernetes manifests, or Helm releases in the `k8s/` directory.
2. **Commit and Push**: Commit your changes to the Git repository.
3. **Automatic Sync**: FluxCD will detect the changes in the repository and automatically apply them to the Kubernetes cluster.
4. **Force Sync (Optional)**: To apply changes immediately without waiting for the next sync interval, you can run `python cli/main.py flux update-now`.

### Secret Management

Secrets are managed using [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets). The process is:

1. Create or modify a raw secret file (e.g., `my-secret.secretraw.yaml`).
2. Use the CLI to encrypt the secret: `python cli/main.py kubeseal`.
3. This generates a sealed secret file, which can be safely committed to the repository. FluxCD will deploy it, and the Sealed Secrets controller in the cluster will decrypt it.
