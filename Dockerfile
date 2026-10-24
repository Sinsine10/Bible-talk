
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/data/hf

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY biblerag ./biblerag
COPY data/people.json ./data/people.json
COPY data/bible/en_kjv.json ./data/bible/en_kjv.json

EXPOSE 8000

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
