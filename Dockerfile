FROM python:3.12-slim AS builder
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="/opt/venv/bin:$PATH"
RUN /opt/venv/bin/python -m pip install --no-cache-dir --upgrade "pip==26.2.1"
WORKDIR /build
COPY requirements.lock ./requirements.lock
RUN pip install --no-cache-dir --requirement requirements.lock

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*
RUN /usr/local/bin/python -m pip install --no-cache-dir --upgrade "pip==26.2.1"
RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /opt/venv /opt/venv
COPY app/ ./app/
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
