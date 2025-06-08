FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

RUN pip install dvc dvc-s3 python-jose

EXPOSE 8080

CMD ["python", "api.py"]
