from metamask import Metamask
from metamask.config import Config, get_config
from metamask.schema import Units

CFG: Config = get_config()

metamask = Metamask(CFG, network=CFG.LINEA_GOERLI_NET)


if __name__ == "__main__":
    metamask.send_transaction(chain_id=CFG.LINEA_TEST_NETWORK_ID, coin=Units.eth.value)
