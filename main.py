import sys

from metamask import Metamask
from metamask.config import Config, get_config

CFG: Config = get_config()


def main():
    """
    Run Metamask with the specified network.

    Args:
        sys.argv[1] (str, optional): The network to connect to. Can be 'ether' or 'polygon'.
            Defaults to CFG.ETHER_NET if not provided.
    """
    network = sys.argv[1] if len(sys.argv) > 1 else CFG.ETHER_NET
    metamask = Metamask(CFG, network=network)
    metamask.run()


if __name__ == "__main__":
    main()
