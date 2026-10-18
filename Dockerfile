FROM python:3.12-slim
WORKDIR /app
COPY requirements-tool.txt .
RUN pip install --no-cache-dir -r requirements-tool.txt
COPY scripts/ scripts/
CMD ["python", "scripts/hello_pipeline.py"]
