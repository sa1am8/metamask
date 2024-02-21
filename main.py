from metamask import Metamask
from metamask.config import Config, get_config

CFG: Config = get_config()
metamask = Metamask(CFG)


if __name__ == "__main__":
    metamask.run()
