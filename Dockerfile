FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
        PYTHONUNBUFFERED=1 \
        PYTHONPATH=/app/src

WORKDIR /app

# Install dependencies
COPY requirements-tool.txt .
RUN pip install --no-cache-dir -r requirements-tool.txt

# Create non-root user
RUN useradd --create-home student

# Copy code and scripts
COPY src/ src/
COPY scripts/pipeline/ scripts/pipeline/

USER student

# Run the synthetic demo by default
CMD ["python", "scripts/pipeline/demo_synthetic.py"]