
#!/bin/sh
set -e

mkdir -p /app/data/index /app/data/bible

if [ ! -d /app/data/index ] || [ -z "$(ls -A /app/data/index 2>/dev/null)" ]; then
  python -m biblerag ingest
fi

exec python -m biblerag serve --host 0.0.0.0 --port "${PORT:-8000}"
