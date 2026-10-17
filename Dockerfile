# UNIFORM Hermetic Verification Container
# Provides 100% reproducible bit-for-bit environment for Python, Rust, and Lean 4 verification.

FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV SHELL=/bin/bash
ENV PATH="/root/.cargo/bin:/root/.elan/bin:/root/.local/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    pkg-config \
    libssl-dev \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install Rust toolchain
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable

# Install uv (astral-sh fast Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Install elan (Lean 4 version manager)
RUN curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y --default-toolchain none

WORKDIR /workspace
COPY . /workspace

# Install Python dependencies
RUN uv sync --extra dev

# Run Rust tests
RUN cargo test --manifest-path rust-scanner/Cargo.toml --release

# Setup and build Lean 4 package
RUN cd lean && elan default $(cat lean-toolchain) && lake build

# Run complete scientific verification suite
CMD ["uv", "run", "python", "scripts/reproduce_all.py"]
