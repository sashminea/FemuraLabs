FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PYTHONPATH=/app/src

WORKDIR /app
	
COPY requirements-tool.txt .
RUN pip install --no-cache-dir -r requirements-tool.txt

RUN useradd --create-home student

COPY src/ src/

USER student

EXPOSE 8000

CMD ["python", "-m", "femuralabs.toolkit.cli"]

