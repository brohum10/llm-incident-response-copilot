FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY incident_copilot ./incident_copilot
COPY runbooks ./runbooks
COPY evals ./evals
RUN pip install --no-cache-dir .

EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "incident_copilot.api:app"]

