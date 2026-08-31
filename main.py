import asyncio
import logging

from aiohttp_socks._errors import ProxyError

from app.bot.bot import main
from app.config.config import Config, load_config

config: Config = load_config()

logging.basicConfig(
    level=config.log.level,
    format=config.log.format
)

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    try:
        asyncio.run(main(config))
    except ProxyError as e:
        port = int(config.proxy.port)
        if port < 10999:
            logger.debug('ProxyError catched. Trying another port...')
            config.proxy.port = str(port + 1)
            asyncio.run(main(config))
        else:
            raise e
