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
    MIN_ETHER_INCOME: float = 0

    INFURA_NETWORK_WSS: str
    INFURA_NETWORK: str

    ETH_NETWORK_ID: int = 1
    POLYGON_NETWORK_ID: int = 137
    LINEA_TEST_NETWORK_ID: int = 59140

    model_config = SettingsConfigDict(
        extra="allow",
        env_file=("project.env", ".env.dev", ".env"),
    )


@lru_cache
def get_config():
    return Config()
