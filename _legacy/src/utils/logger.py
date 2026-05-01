import sys
from pathlib import Path
from loguru import logger
from config.settings import settings


def setup_logger(phase: str = "main") -> None:
    today = __import__("datetime").date.today().isoformat()
    log_dir = Path(settings.log_dir)

    logger.remove()  # Remove default handler

    # Console — human-readable
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
        colorize=True,
    )

    # Phase-specific daily log
    logger.add(
        log_dir / phase / f"{today}.log",
        level="DEBUG",
        rotation="1 day",
        retention="30 days",
        compression="gz",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{line} | {message}",
    )

    # Errors log (all phases share this)
    logger.add(
        log_dir / "error" / f"{today}-error.log",
        level="ERROR",
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} | {message}\n{exception}",
    )
