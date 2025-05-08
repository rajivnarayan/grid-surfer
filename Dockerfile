FROM python:3.12-slim-bookworm AS builder
# Copy uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Setup a non-root user
# See: https://code.visualstudio.com/remote/advancedcontainers/add-nonroot-user
ARG USERNAME=node
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    #
    # [Optional] Add sudo support. Omit if you don't need to install software after connecting.
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Change working directory
WORKDIR /app

ENV PATH="/root/.local/bin:${PATH}"

# Copy the project into the image
ADD . /app
# Install dependencies
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes git && \
    uv sync --locked

# Application port
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# [Optional] Set the default user. Omit if you want to keep the default as root.
USER $USERNAME

ENTRYPOINT ["uv", "run", "streamlit", "run", "app.py"]
