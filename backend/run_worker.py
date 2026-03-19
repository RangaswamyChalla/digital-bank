#!/usr/bin/env python
"""
ARQ Worker entry point for Digital Bank background jobs.

Run with:
    arq app.worker_config.WorkerSettings

Or for development with auto-reload:
    python -m arq app.worker_config.WorkerSettings
"""
import asyncio
import logging
from arq import run_worker

from app.worker_config import WorkerSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


if __name__ == "__main__":
    asyncio.run(run_worker(WorkerSettings))
