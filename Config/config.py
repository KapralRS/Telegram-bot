from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str


@dataclass
class Config:
    bot: TgBot


def load_config() -> Config:
    env: Env = Env()
    env.read_env()

    return Config(bot=TgBot(token=env("BOT_TOKEN")))
