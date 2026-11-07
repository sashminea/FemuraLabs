FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (for Docker layer caching)
COPY requirements-tool.txt .
RUN pip install --no-cache-dir -r requirements-tool.txt

# Create non-root user for security
RUN useradd --create-home student

# Copy the package definition, source code, and all scripts
COPY pyproject.toml .
COPY src/ src/
COPY scripts/ scripts/

# Install the local package (--no-deps because requirements are already installed).
# This registers the `femuralabs` command globally.
RUN pip install --no-cache-dir --no-deps .

# Switch to the non-root user
USER student

# Default command: Show the CLI help menu
CMD ["femuralabs", "--help"]