FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

RUN pip install dvc dvc-s3 python-jose

RUN pip install python-multipart

RUN pip install pika

EXPOSE 8080

CMD ["python", "api.py"]
