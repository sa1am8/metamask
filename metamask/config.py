from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from web3.types import ENS


class Config(BaseSettings):
    PRIVATE_KEY_SENDER: str
    ADDRESS_SENDER: ENS
    ADDRESS_RECEIVER: str
    VALUE_ETHER: float
    GAS_LIMIT: int
    INFURA_PROJECT_ID: str

    ETH_NETWORK: int = 1
    POLYGON_NETWORK: int = 137

    model_config = SettingsConfigDict(
        extra="allow",
        env_file=("project.env", ".env.dev", ".env"),
    )


@lru_cache
def get_config():
    return Config()
