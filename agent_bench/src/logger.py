from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install
import logging
import os

install()
del install

LOG_LEVEL = logging.DEBUG if os.getenv("AGENT_DEBUG") else logging.INFO
logger = logging.getLogger("AGENT_MAIN")
logger.propagate = False
logger.setLevel(LOG_LEVEL)
logger.addHandler(
    RichHandler(level=LOG_LEVEL, console=Console(stderr=True), show_time=True, show_path=True, rich_tracebacks=True)
)
# add a file handler

# file_handler = logging.FileHandler("agent.log")
# file_handler.setLevel(logging.DEBUG)
# file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(level)s - %(message)s"))
# logger.addHandler(file_handler)

# disable logging for specific modules
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("root").setLevel(logging.WARNING)

logger.info("Agent initialized")