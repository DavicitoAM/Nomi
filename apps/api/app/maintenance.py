"""Explicit bounded credential cleanup. Never removes financial records or idempotency."""

import argparse
import json

from app.shared.uow import SqlUnitOfWork


def cleanup(apply=False):
    with SqlUnitOfWork() as uow:
        result = uow.identity.cleanup_expired(apply)
        if apply:
            uow.commit()
        return {"mode": "apply" if apply else "dry-run", "tables": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Delete up to 1000 old rows per table")
    print(json.dumps(cleanup(parser.parse_args().apply)))
