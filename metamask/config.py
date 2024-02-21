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
    MIN_ETHER_INCOME: float = 0.0001
    # INFURA_NETWORK_URL: str = "https://mainnet.infura.io/v3/"
    POLYGON_NETWORK: str = "https://rpc-mumbai.polygon.technology"
    LINEA_NETWORK: str = "https://rpc.goerli.linea.build"

    ETH_NETWORK_ID: int = 1
    POLYGON_NETWORK_ID: int = 137

    @property
    def INFURA_NETWORK_WSS(self):
        return "wss://goerli.infura.io/ws/v3/" + self.INFURA_PROJECT_ID

    @property
    def INFURA_NETWORK(self):
        return "https://goerli.infura.io/v3/" + self.INFURA_PROJECT_ID

    model_config = SettingsConfigDict(
        extra="allow",
        env_file=("project.env", ".env.dev", ".env"),
    )


@lru_cache
def get_config():
    return Config()
