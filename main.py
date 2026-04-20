import asyncio
import logging

from app.bot import main
from app.config.config import Config, load_config


config: Config = load_config()

logging.basicConfig(
    level=config.log.level,
    format=config.log.format
)

asyncio.run(main(config))