import json
from typing import cast

import websocket
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import TransactionNotFound
from web3.middleware import geth_poa_middleware
from web3.types import ENS, HexBytes, HexStr, Wei

from .config import GMEE_ABI_ETHER, GMEE_ABI_POLYGON, Config
from .logger import log
from .schema import Transaction, Units


class Metamask:
    w3: Web3
    config: Config

    def __init__(self, config: Config, network: str):
        self.network = network

        if network not in [config.ETHER_NET, config.POLYGON_NET]:
            raise ValueError(
                f"Network must be one of {config.ETHER_NET}, {config.POLYGON_NET}"
            )
        if network == config.ETHER_NET:
            self.network_url: str = config.ETHER_NETWORK
            self.network_wss: str = config.ETHER_NETWORK_WSS
            self.gmee_abi: dict = GMEE_ABI_ETHER
            self.gmee_contract: str = config.GMEE_CONTRACT_ETHER
        else:
            self.network_url = config.POLYGON_NETWORK
            self.network_wss = config.POLYGON_NETWORK_WSS
            self.gmee_abi = GMEE_ABI_POLYGON
            self.gmee_contract = config.GMEE_CONTRACT_POLYGON

        self.w3: Web3 = Web3(Web3.HTTPProvider(self.network_url))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.config: Config = config

    def send_transaction(
        self,
        private_key_sender: str | None = None,
        address_sender: ENS | None = None,
        address_receiver: str | None = None,
        value: float | None = None,
        gas_limit: int | None = None,
        chain_id: int | None = None,
        coin: str | None = None,
    ) -> str:
        """Send a transaction to the Ethereum network. Returns the transaction hash.

        Args:
            private_key_sender (str, optional): private key of sender for signing. Defaults to self.config.PRIVATE_KEY_SENDER.
            address_sender (ENS, optional): address of sender. Defaults to self.config.ADDRESS_SENDER.
            address_receiver (str, optional): address of receiver. Defaults to self.config.ADDRESS_RECEIVER.
            value (float, optional): value of ether to send. Defaults to self.config.VALUE. Can't be 0.
            gas_limit (int, optional): Gas limit to use. Defaults to self.config.GAS_LIMIT. Can't be 0.
            chain_id (int, optional): ID of network for transaction. Defaults to self.config.ETH_NETWORK_ID (1). Also could be used self.config.POLYGON_NETWORK_ID (137). Can't be 0.
            coin (str, optional): Coin name, must be one of units. Defaults to None.

        Returns:
            str: transaction hash
        """
        private_key_sender = private_key_sender or self.config.PRIVATE_KEY_SENDER
        address_sender = address_sender or self.config.ADDRESS_SENDER
        address_receiver = address_receiver or self.config.ADDRESS_RECEIVER
        value = value or self.config.VALUE
        gas_limit = gas_limit or self.config.GAS_LIMIT
        chain_id = chain_id or self.config.LINEA_TEST_NETWORK_ID
        coin = coin or Units.gmee.value

        if coin not in Units.__members__.keys():
            raise ValueError(
                f"Coin must be one of units: {', '.join(Units.__members__.keys())}"
            )

        if chain_id not in [
            self.config.ETH_NETWORK_ID,
            self.config.POLYGON_NETWORK_ID,
            self.config.LINEA_TEST_NETWORK_ID,
        ]:
            raise ValueError(
                f"Chain ID must be one of {self.config.ETH_NETWORK_ID}, {self.config.POLYGON_NETWORK_ID}, {self.config.LINEA_TEST_NETWORK_ID}"
            )

        value = Web3.to_wei(value, "ether")

        nonce: int = self.w3.eth.get_transaction_count(address_sender)
        gas_price: int = self.w3.eth.gas_price

        transaction = Transaction(
            nonce=nonce,
            to=address_receiver,
            value=value,
            gas=gas_limit,
            gasPrice=gas_price,
            chainId=chain_id,
        ).model_dump()

        if coin == Units.gmee.value:
            gmee_contract: Contract = self.w3.eth.contract(  # type: ignore
                address=self.gmee_contract,
                abi=self.gmee_abi,
            )

            transaction = gmee_contract.functions.transfer(
                address_receiver, value
            ).build_transaction(
                {
                    "from": address_sender,
                    "chainId": chain_id,
                    "gas": gas_limit,
                    "nonce": nonce,  # type: ignore
                    "gasPrice": cast(Wei, gas_price),
                }
            )

        signed_txn = self.w3.eth.account.sign_transaction(
            transaction, private_key_sender
        )
        try:
            tx_hash: HexBytes = self.w3.eth.send_raw_transaction(
                signed_txn.rawTransaction
            )
        except ValueError as e:
            log(log.ERROR, "Transaction failed: %s", e)
            if "insufficient funds" in str(e):
                log(
                    log.ERROR,
                    "Insufficient funds. You have %s ether, when need %s ether.",
                    self.w3.from_wei(self.w3.eth.get_balance(address_sender), "ether"),
                    self.w3.from_wei(int(e.args[0]["message"].split(" ")[-1]), "ether"),
                )
                return ""
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
                    log(log.DEBUG, "Transaction not found - %s", result)
                    return
                log(log.DEBUG, "Found new block - %s", tx)
                if (
                    tx.to == self.config.ADDRESS_SENDER
                ) and tx.value > self.config.MIN_INCOME:
                    log(log.INFO, "Transaction to us - %s", tx)
                    self.w3.eth.get_balance(self.config.ADDRESS_SENDER)
                    self.send_transaction(
                        chain_id=self.w3.eth.chain_id,
                        value=self.w3.eth.get_balance(self.config.ADDRESS_SENDER),
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
            self.network_wss,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
        )

        ws.run_forever()
