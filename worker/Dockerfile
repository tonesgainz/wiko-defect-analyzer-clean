FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
COPY worker/requirements.txt ./worker-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r worker-requirements.txt

COPY . .

CMD ["python", "-m", "worker.main"]
