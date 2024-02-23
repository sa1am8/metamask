import json
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from web3.types import ENS

GMEE_ABI_ETHER: dict = json.loads(open("metamask/data/gmee_abi_ether.json").read())
GMEE_ABI_POLYGON: dict = json.loads(open("metamask/data/gmee_abi_polygon.json").read())


class Config(BaseSettings):
    PRIVATE_KEY_SENDER: str
    ADDRESS_SENDER: ENS
    ADDRESS_RECEIVER: str
    VALUE: float
    GAS_LIMIT: int
    INFURA_PROJECT_ID: str
    MIN_ETHER_INCOME: float = 0

    ETHER_NETWORK_WSS: str
    ETHER_NETWORK: str
    POLYGON_NETWORK_WSS: str
    POLYGON_NETWORK: str
    LINEA_GOERLI_NETWORK: str
    LINEA_GOERLI_NETWORK_WSS: str

    ETH_NETWORK_ID: int = 1
    POLYGON_NETWORK_ID: int = 137
    LINEA_TEST_NETWORK_ID: int = 59140

    GMEE_CONTRACT_ETHER: str = "0xD9016A907Dc0ECfA3ca425ab20B6b785B42F2373"
    GMEE_CONTRACT_POLYGON: str = "0xcf32822ff397Ef82425153a9dcb726E5fF61DCA7"

    ETHER_NET: str = "ether"
    POLYGON_NET: str = "polygon"
    LINEA_GOERLI_NET: str = "linea_goerli"

    model_config = SettingsConfigDict(
        extra="allow",
        env_file=("project.env", ".env.dev", ".env"),
    )


@lru_cache
def get_config():
    return Config()
