# ARM64-compatible slim Python base image
FROM python:3.10-slim

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Create non-root user with specific UID/GID
RUN groupadd -r sandbox -g 1000 && \
    useradd --no-log-init -r -g sandbox -u 1000 sandbox && \
    mkdir -p /home/sandbox && \
    chown -R sandbox:sandbox /home/sandbox

WORKDIR /app

# Copy dependency files first (for better layer caching)
COPY --chown=sandbox:sandbox pyproject.toml pyproject.toml

# Install Python dependencies using pip
RUN pip install --no-cache-dir \
    "autogen-core>=0.4.0" \
    "autogen-agentchat>=0.4.0" \
    "autogen-ext[openai]>=0.4.0" \
    "python-dotenv>=1.0.0" \
    "grpcio>=1.60.0" \
    "grpcio-tools>=1.60.0"

# Copy application code
COPY --chown=sandbox:sandbox world.py world.py
COPY --chown=sandbox:sandbox agent.py agent.py
COPY --chown=sandbox:sandbox creator.py creator.py
COPY --chown=sandbox:sandbox messages.py messages.py
COPY --chown=sandbox:sandbox metrics.py metrics.py
COPY --chown=sandbox:sandbox validator.py validator.py


# Create necessary directories with proper permissions
RUN mkdir -p /runtime /assessments && \
    chown -R sandbox:sandbox /runtime /assessments

# Switch to non-root user
USER sandbox

# Set home directory
ENV HOME=/home/sandbox

WORKDIR /app

# Health check (optional but recommended)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)" || exit 1

# Default run command
CMD ["python", "world.py"]