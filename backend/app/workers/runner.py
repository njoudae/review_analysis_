import argparse
import logging
import time

from sqlalchemy import select

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.models import CollectionRun, RunState
from app.services.processing import process_run


logger = logging.getLogger(__name__)


def claim_run() -> str | None:
    with SessionLocal() as db:
        with db.begin():
            run = db.scalar(
                select(CollectionRun)
                .where(CollectionRun.status == RunState.STARTED)
                .order_by(CollectionRun.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if not run:
                return None
            run.status = RunState.COLLECTING
            return run.id


def run_once() -> bool:
    run_id = claim_run()
    if not run_id:
        return False
    with SessionLocal() as db:
        try:
            process_run(db, run_id)
        except Exception:
            logger.exception("worker_run_failed", extra={"run_id": run_id})
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Process queued collection runs")
    parser.add_argument("--once", action="store_true", help="Process at most one queued run and exit")
    args = parser.parse_args()
    configure_logging()
    if args.once:
        run_once()
        return
    logger.info("worker_started", extra={"poll_seconds": settings.worker_poll_seconds})
    while True:
        worked = run_once()
        if not worked:
            time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    main()

