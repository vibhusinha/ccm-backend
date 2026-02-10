FROM python:3.12-slim

ARG SERVICE_NAME=auth
ENV SERVICE_NAME=${SERVICE_NAME}

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY app/ app/
COPY services/ services/

EXPOSE 8000

CMD uvicorn services.${SERVICE_NAME}.main:app --host 0.0.0.0 --port 8000
