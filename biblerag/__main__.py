import argparse

import uvicorn

from biblerag.config import settings
from biblerag.ingest import ingest


def main() -> None:
    parser = argparse.ArgumentParser(prog="biblerag")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ingest", help="Download KJV and build the vector index")
    serve = sub.add_parser("serve", help="Run the HTTP API")
    serve.add_argument("--host", default=settings.host)
    serve.add_argument("--port", type=int, default=settings.port)
    args = parser.parse_args()
    if args.cmd == "ingest":
        print(ingest())
        return
    uvicorn.run("biblerag.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
