# Stage 1, builder environment
FROM python:3.12-slim-bookworm AS builder

# Copy uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install build dependencies including git
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes \
    git \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Change working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies (git dependency needs git available)
RUN uv sync --locked --no-dev

# Stage 2. Runtime environment
FROM python:3.12-slim-bookworm AS runtime

# Setup a non-root user
ARG USERNAME=node
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user without sudo (not needed in production)
RUN groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

# Install only runtime dependencies
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Change working directory
WORKDIR /app

# Copy virtual environment from builder (includes all dependencies)
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app.py ./
COPY src/ ./src/
COPY assets/ ./assets/
COPY data/ ./data/
COPY .streamlit/ ./.streamlit/

# Generate version file during build
ARG VERSION=latest
RUN echo "${VERSION}" > version.txt

# Set PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Application port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Set non-root user
USER $USERNAME

# Use exec form for better signal handling
ENTRYPOINT ["python", "-m", "streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
