import json

import websocket
from web3 import Web3
from web3.exceptions import TransactionNotFound
from web3.middleware import geth_poa_middleware
from web3.types import HexBytes, HexStr

from .config import Config
from .logger import log
from .schema import Transaction


class Metamask:
    w3: Web3
    config: Config

    def __init__(self, config: Config):
        self.w3: Web3 = Web3(Web3.HTTPProvider(config.LINEA_NETWORK))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.config = config

    def send_transaction(
        self,
    ) -> str:
        """Send a transaction to the Ethereum network. Returns the transaction hash.

        Args:
            private_key_sender (str, optional): private key of sender for signing. Defaults to self.config.PRIVATE_KEY_SENDER.
            address_sender (ENS, optional): address of sender. Defaults to self.config.ADDRESS_SENDER.
            address_receiver (str, optional): address of receiver. Defaults to self.config.ADDRESS_RECEIVER.
            value_ether (float, optional): value of ether to send. Defaults to self.config.VALUE_ETHER.
            gas_limit (int, optional): Gas limit to use. Defaults to self.config.GAS_LIMIT.
            chain_id (int, optional): ID of network for transaction. Defaults to self.config.ETH_NETWORK_ID (1). Also could be used self.config.POLYGON_NETWORK_ID (137).

        Returns:
            str: transaction hash
        """
        private_key_sender = self.config.PRIVATE_KEY_SENDER
        address_sender = self.config.ADDRESS_SENDER
        address_receiver = self.config.ADDRESS_RECEIVER
        value_ether = self.config.VALUE_ETHER
        gas_limit = self.config.GAS_LIMIT
        chain_id = self.config.ETH_NETWORK_ID

        nonce: int = self.w3.eth.get_transaction_count(address_sender)
        gas_price: int = self.w3.eth.gas_price

        value: int = Web3.to_wei(value_ether, "ether")

        transaction = Transaction(
            nonce=nonce,
            to=address_receiver,
            value=value,
            gas=gas_limit,
            gasPrice=gas_price,
            chainId=chain_id,
        )
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction.model_dump(), private_key_sender
        )
        try:
            tx_hash: HexBytes = self.w3.eth.send_raw_transaction(
                signed_txn.rawTransaction
            )
        except ValueError as e:
            log(log.ERROR, "Transaction failed: %s", e)
            raise e
        log(log.INFO, "Transaction hash: %s", tx_hash.hex())

        self.w3.eth.wait_for_transaction_receipt(HexStr(tx_hash.hex()), timeout=120)
        log(log.INFO, "Transaction confirmed: %s", tx_hash.hex())
        return tx_hash.hex()

    def run(self):
        # websocket.enableTrace(True)
        def on_message(ws, message):
            message = json.loads(message)
            if "params" in message and "result" in message["params"]:
                result = message["params"]["result"]
                try:
                    tx = self.w3.eth.get_transaction(result)
                except TransactionNotFound:
                    log(log.INFO, "Transaction not found - %s", result)
                    return
                log(log.INFO, "Found new block - %s", tx)
                if (
                    tx.to == self.config.ADDRESS_SENDER
                    and tx.value > self.config.MIN_ETHER_INCOME
                ):
                    log(log.INFO, "Transaction to us - %s", tx)
                    self.send_transaction(
                        address_sender=self.config.ADDRESS_SENDER,
                        address_receiver=self.config.ADDRESS_RECEIVER,
                        ETHER_INCOME=self.config.ETHER_INCOME,
                        gas_limit=self.config.GAS_LIMIT,
                        chain_id=self.config.ETH_NETWORK_ID,
                    )

        def on_error(ws: websocket.WebSocket, error):
            log(log.ERROR, error)

        def on_close(ws: websocket.WebSocket, close_status_code, close_msg):
            log(log.CRITICAL, "WebSocket closed")

        def on_open(ws):
            log(log.INFO, "WebSocket opened")

            subscription_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_subscribe",
                "params": ["newPendingTransactions"],
            }
            ws.send(json.dumps(subscription_request))

        ws = websocket.WebSocketApp(
            self.config.INFURA_NETWORK_WSS,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
        )

        ws.run_forever()
