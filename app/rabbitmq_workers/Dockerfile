FROM python:3.11-slim

WORKDIR /app

COPY ./app/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY ./app /app

ENV PYTHONPATH=/app

CMD ["python", "rabbitmq_workers/main_worker.py"]