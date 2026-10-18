FROM python:3.12-slim
ENV PYTHONPATH=/app/src
WORKDIR /app
COPY requirements-tool.txt .
RUN pip install --no-cache-dir -r requirements-tool.txt
COPY src/ src/
COPY scripts/ scripts/
CMD ["python", "scripts/hello_pipeline.py"]
