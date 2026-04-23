import logging
from dataclasses import dataclass
from environs import Env

logger = logging.getLogger(__name__)


@dataclass
class TgBot:
    bot_token: str

@dataclass
class LogSettings:
    level: str
    format: str

@dataclass
class ProxySettings:
    login: str
    password: str
    address: str
    port: str

    @property
    def proxy_url(self):
        return f'socks5://{self.login}:{self.password}@{self.address}:{self.port}'

@dataclass
class DatabaseSettings:
    path: str

@dataclass
class Config:
    tg_bot: TgBot
    log: LogSettings
    proxy: ProxySettings
    db: DatabaseSettings

def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)

    tg_bot = TgBot(
        bot_token=env('BOT_TOKEN')
    )
    log = LogSettings(
        level=env('LOG_LEVEL'),
        format=env('LOG_FORMAT')
    )
    proxy = ProxySettings(
        login=env('PROXY_LOGIN'),
        password=env('PROXY_PASSWORD'),
        address=env('PROXY_ADDRESS'),
        port=env('PROXY_PORT')
    )
    db = DatabaseSettings(
        path=env('DB_PATH')
    )

    logger.info('Configuration loaded successfully.')

    return Config(
        tg_bot=tg_bot,
        log=log,
        proxy=proxy,
        db=db
    )