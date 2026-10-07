"""Run `python -m app.worker`, or use --once for a bounded mail batch."""

import argparse
import logging
import time

from sqlalchemy import update

from app.core.database import session_factory
from app.modules.identity.application.mail import PURPOSES, process_next_mail
from app.modules.identity.infrastructure.mail_transport import MailTransport
from app.modules.identity.infrastructure.token_cipher import delivery_cipher
from app.shared.context import now
from app.shared.models import OutboxRow
from app.shared.uow import SqlUnitOfWork


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.limit <= 1000:
        parser.error("limit must be 1..1000")
    delivery_cipher()  # Validate a persistent key before claiming anything.
    if args.retry_failed:
        with session_factory.begin() as db:
            db.execute(
                update(OutboxRow)
                .where(
                    OutboxRow.event_type.in_(PURPOSES),
                    OutboxRow.processed_at.is_(None),
                    OutboxRow.attempts >= 8,
                )
                .values(attempts=0, available_at=now(), last_error_code=None)
            )
    transport = MailTransport()
    try:
        while True:
            processed = 0
            try:
                while processed < args.limit and process_next_mail(SqlUnitOfWork(), transport):
                    processed += 1
            except Exception:
                logging.getLogger("nomi.worker").error("worker_iteration_failed")
                if args.once:
                    raise SystemExit(1) from None
            if args.once:
                print(f"Mail events handled: {processed}")
                return
            time.sleep(2)
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
