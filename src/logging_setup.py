"""Logging helpers for the command-line pipeline."""

from __future__ import annotations

import logging


def configure_logging(verbosity: int = 0) -> None:
    """Configure root logging based on the CLI verbosity level."""

    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
