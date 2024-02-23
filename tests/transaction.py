from metamask import Metamask
from metamask.config import Config, get_config
from metamask.schema import Units

CFG: Config = get_config()
# there exists linea goerli network
metamask = Metamask(CFG, network=CFG.ETHER_NET)


if __name__ == "__main__":
    metamask.send_transaction(chain_id=CFG.ETH_NETWORK_ID, coin=Units.gmee.value)
