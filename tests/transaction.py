from metamask import Metamask
from metamask.config import Config, get_config

CFG: Config = get_config()
metamask = Metamask(CFG)


if __name__ == "__main__":
    metamask.send_transaction(chain_id=CFG.LINEA_TEST_NETWORK_ID)
