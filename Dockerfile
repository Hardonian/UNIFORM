# UNIFORM pinned release-verification container.
# Network-fetched toolchains are version-pinned, but image digests and host CPU timing
# remain outside the scientific certificate and are not claimed to be bit-for-bit stable.

FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV SHELL=/bin/bash
ENV PATH="/root/.cargo/bin:/root/.elan/bin:/root/.local/bin:$PATH"
ARG RUST_TOOLCHAIN=1.98.1
ARG UV_VERSION=0.9.5

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
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- \
    -y --profile minimal --default-toolchain "${RUST_TOOLCHAIN}"

# Install uv (astral-sh fast Python package manager)
RUN curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | sh

# Install elan (Lean 4 version manager)
RUN curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y --default-toolchain none

WORKDIR /workspace
COPY . /workspace

# Install Python dependencies
RUN uv sync --frozen --extra dev --extra solvers

# Run Rust tests
RUN cargo test --manifest-path rust-scanner/Cargo.toml --release

# Setup and build Lean 4 package
RUN cd lean && elan default $(cat lean-toolchain) && lake build

# Run complete scientific verification suite
CMD ["uv", "run", "python", "scripts/reproduce_all.py"]
