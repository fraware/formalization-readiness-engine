from __future__ import annotations

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "packages" / "fre_core" / "src"))


def main() -> None:
    from rq import Worker

    from fre_core.jobs.queue import JobQueue

    q = JobQueue()
    queue = q._get_queue()
    Worker([queue], connection=queue.connection).work(with_scheduler=False)


if __name__ == "__main__":
    main()
