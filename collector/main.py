"""Collector main entry point - runs scheduled model tests."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import load_config
from shared.db import init_db, save_metric
from collector.tester import test_all_models

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def collect_once(config) -> int:
    """Run a single collection cycle.

    Args:
        config: Configuration object.

    Returns:
        Number of models tested.
    """
    logger.info("Starting collection cycle...")

    results = await test_all_models(config.providers, config.collector)

    success_count = 0
    for result in results:
        try:
            save_metric(result)

            status = "✓" if result.success else "✗"
            if result.success:
                speed = f"{result.tokens_per_second:.1f} t/s" if result.tokens_per_second else "N/A"
                ttft = f"{result.ttft_ms:.0f}ms" if result.ttft_ms else "N/A"
                logger.info(f"{status} {result.provider_name}/{result.model_id}: {speed}, TTFT: {ttft}")
                success_count += 1
            else:
                logger.warning(f"{status} {result.provider_name}/{result.model_id}: {result.error_message}")

        except Exception as e:
            logger.error(f"Failed to save metric for {result.provider_name}/{result.model_id}: {e}")

    logger.info(f"Collection cycle complete. {success_count}/{len(results)} successful.")
    return len(results)


async def run_collector(interval_minutes: int = 5, once: bool = False) -> None:
    """Run collector on a schedule.

    Args:
        interval_minutes: Interval between collection cycles.
        once: Run only once and exit.
    """
    config = load_config()

    # Initialize database
    logger.info("Initializing database...")
    init_db(config)

    # Count configured models
    total_models = sum(len(p.models) for p in config.providers)
    logger.info(f"Monitoring {len(config.providers)} providers, {total_models} models")

    if once:
        await collect_once(config)
        return

    logger.info(f"Starting collector with {interval_minutes} minute interval")

    while True:
        try:
            await collect_once(config)
        except Exception as e:
            logger.error(f"Collection cycle failed: {e}")

        logger.info(f"Sleeping for {interval_minutes} minutes...")
        await asyncio.sleep(interval_minutes * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LLM Speed Monitor Collector")
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Collection interval in minutes (overrides config)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit",
    )
    args = parser.parse_args()

    config = load_config()
    interval = args.interval or config.collector.interval_minutes

    try:
        asyncio.run(run_collector(interval, once=args.once))
    except KeyboardInterrupt:
        logger.info("Collector stopped by user")


if __name__ == "__main__":
    main()
