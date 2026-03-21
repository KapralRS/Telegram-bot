from dataclasses import dataclass
from environs import Env

LOG_LEVEL = "DEBUG"
LOG_FORMAT = "[{asctime}] #{levelname:8} {filename}:{lineno} - {name} - {message}"

env: Env = Env()
env.read_env()


@dataclass
class TgBot:
    token: str


@dataclass
class LogSettings:
    level: str
    format: str


@dataclass
class Config:
    bot: TgBot
    log: LogSettings


def load_config(path: str | None = None) -> Config:

    return Config(
        bot=TgBot(token=env("8250500786:AAHHma7KiuyyDTf-zp7mI2oqJNbOtZnDpME")),
        log=LogSettings(level=LOG_LEVEL, format=LOG_FORMAT),
    )
