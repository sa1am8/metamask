from web3 import Web3
from web3.datastructures import AttributeDict
from web3.middleware import geth_poa_middleware
from web3.types import ENS, HexBytes

from config import Config, get_config
from logger import log
from schema import Transaction

CFG: Config = get_config()

w3: Web3 = Web3(
    Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{CFG.INFURA_PROJECT_ID}")
)
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# for polygon network might be used polygon library


def send_transaction(
    private_key_sender: str = CFG.PRIVATE_KEY_SENDER,
    address_sender: ENS = CFG.ADDRESS_SENDER,
    address_receiver: str = CFG.ADDRESS_RECEIVER,
    value_ether: float = CFG.VALUE_ETHER,
    gas_limit: int = CFG.GAS_LIMIT,
    chain_id: int = CFG.ETH_NETWORK,
) -> str:
    """Send a transaction to the Ethereum network. Returns the transaction hash.

    Args:
        private_key_sender (str, optional): private key of sender for signing. Defaults to CFG.PRIVATE_KEY_SENDER.
        address_sender (ENS, optional): address of sender. Defaults to CFG.ADDRESS_SENDER.
        address_receiver (str, optional): address of receiver. Defaults to CFG.ADDRESS_RECEIVER.
        value_ether (float, optional): value of ether to send. Defaults to CFG.VALUE_ETHER.
        gas_limit (int, optional): Gas limit to use. Defaults to CFG.GAS_LIMIT.
        chain_id (int, optional): ID of network for transaction. Defaults to CFG.ETH_NETWORK (1). Also could be used CFG.POLYGON_NETWORK (137).

    Returns:
        str: transaction hash
    """

    nonce: int = w3.eth.get_transaction_count(address_sender)
    gas_price: int = w3.eth.gas_price

    value: int = Web3.to_wei(value_ether, "ether")

    transaction: Transaction = Transaction(
        nonce=nonce,
        to=address_receiver,
        value=value,
        gas=gas_limit,
        gasPrice=gas_price,
        chainId=chain_id,
    )
    signed_txn: AttributeDict = w3.eth.account.sign_transaction(
        transaction.model_dump(), private_key_sender
    )
    try:
        tx_hash: HexBytes = w3.eth.send_raw_transaction(signed_txn.rawTransaction)  # type: ignore
    except ValueError as e:
        log(log.ERROR, "Transaction failed: %s", e)
        raise e
    log(log.INFO, "Transaction hash: %s", tx_hash.hex())

    return tx_hash.hex()


send_transaction(value_ether=0)
