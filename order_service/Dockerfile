FROM python:3.12-slim AS builder
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /build
COPY order_service/requirements.lock ./requirements.lock
RUN pip install --no-cache-dir --requirement requirements.lock

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /opt/venv /opt/venv
COPY order_service/main.py order_service/models.py ./
COPY shared/ ./shared/
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
