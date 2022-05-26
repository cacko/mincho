import logging
from os import environ

logging.basicConfig(
    level=getattr(logging, environ.get("MINCHO_LOG_LEVEL", "INFO")),
    format="%(filename)s %(message)s",
    datefmt="MINCH %H:%M:%S",
)
log = logging.getLogger("BOTYO")
