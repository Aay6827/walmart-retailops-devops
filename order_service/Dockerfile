FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY order_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY order_service/main.py order_service/models.py ./
COPY shared/ ./shared/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
