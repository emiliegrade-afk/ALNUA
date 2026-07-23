#!/usr/bin/env python3
"""Start RQ worker for ALNUA Hub background tasks."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from rq import Worker
        from services.redis_client import get_redis

        conn = get_redis()
        if conn is None:
            print("❌ REDIS_URL not configured")
            return 1
        worker = Worker(["alnua_default"], connection=conn)
        print("🚀 RQ worker started — queue: alnua_default")
        worker.work()
        return 0
    except ImportError:
        print("pip install rq redis")
        return 1


if __name__ == "__main__":
    sys.exit(main())
