import time
from typing import cast

from web3 import Web3
from web3.contract import Contract
from web3.middleware import geth_poa_middleware
from web3.types import ENS, HexBytes, HexStr, Nonce, TxParams, Wei

from .config import GMEE_ABI_ETHER, GMEE_ABI_POLYGON, Config
from .logger import log
from .schema import Units


class Metamask:
    w3: Web3
    config: Config
    network: str
    network_id: int
    network_url: str
    gmee_abi: dict
    gmee_contract: str

    def __init__(self, config: Config, network: str):
        """Initialize Metamask with the specified network.

        Args:
            config (Config): instance of Config, containing the configuration for Metamask.
            network (str): The network to connect to. Can be 'ether', 'polygon', or 'linea-goerli'.

        Raises:
            ValueError: If the network is not one of 'ether', 'polygon', or 'linea-goerli'.
        """
        self.network = network

        if network not in [
            config.ETHER_NET,
            config.POLYGON_NET,
            config.LINEA_GOERLI_NET,
        ]:
            raise ValueError(
                f"Network must be one of {config.ETHER_NET}, {config.POLYGON_NET}, {config.LINEA_GOERLI_NET}"
            )
        if network == config.ETHER_NET:
            self.network_url: str = config.ETHER_NETWORK
            self.gmee_abi: dict = GMEE_ABI_ETHER
            self.gmee_contract: str = config.GMEE_CONTRACT_ETHER
            self.coin: str = Units.eth.value
        elif network == config.POLYGON_NET:
            self.network_url = config.POLYGON_NETWORK
            self.gmee_abi = GMEE_ABI_POLYGON
            self.gmee_contract = config.GMEE_CONTRACT_POLYGON
            self.coin = Units.matic.value
        else:
            self.network_url = config.LINEA_GOERLI_NETWORK
            self.gmee_abi = GMEE_ABI_ETHER
            self.gmee_contract = config.GMEE_CONTRACT_ETHER
            self.coin = Units.eth.value

        self.w3: Web3 = Web3(Web3.HTTPProvider(self.network_url))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.config: Config = config

    def build_transaction_gmee(
        self,
        address_receiver: str,
        value: float,
        chain_id: int,
        gas_limit: int,
        nonce: int,
        address_sender: ENS,
        gas_price: int,
    ) -> TxParams:
        """Build contract transaction for GMEE token transfer.

        Args:
            address_receiver (str): address of receiver
            value (float): amount of GMEE to send
            chain_id (int): in which network to send transaction
            gas_limit (int): gas limit to use
            nonce (int): nonce of sender
            address_sender (ENS): address of sender
            gas_price (int): gas price to use

        Returns:
            TxParams: transaction model for GMEE token transfer
        """
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
        return TxParams(**transaction)

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

        nonce: Nonce = self.w3.eth.get_transaction_count(address_sender)
        gas_price: Wei = self.w3.eth.gas_price

        transaction = TxParams(  # transaction model for eth (as coin) transfer
            nonce=nonce,
            to=address_receiver,
            value=value,
            gas=gas_limit,
            gasPrice=gas_price,
            chainId=chain_id,
        )

        if coin == Units.gmee.value:
            transaction = self.build_transaction_gmee(
                address_receiver,
                value,
                chain_id,
                gas_limit,
                nonce,
                address_sender,
                gas_price,
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
                try:
                    log(
                        log.ERROR,
                        "Insufficient funds. You have %s ether, when need %s ether.",
                        self.w3.from_wei(
                            self.w3.eth.get_balance(address_sender), "ether"
                        ),
                        self.w3.from_wei(
                            int(e.args[0]["message"].split(" ")[-1]), "ether"
                        ),
                    )
                except ValueError:
                    log(
                        log.ERROR,
                        "Insufficient funds. You have %s ether",
                        self.w3.from_wei(
                            self.w3.eth.get_balance(address_sender), "ether"
                        ),
                    )
                return ""
        log(log.INFO, "Transaction hash: %s", tx_hash.hex())

        self.w3.eth.wait_for_transaction_receipt(HexStr(tx_hash.hex()), timeout=120)
        log(log.INFO, "Transaction confirmed: %s", tx_hash.hex())
        return tx_hash.hex()

    def run(self):
        balance: float = self.w3.from_wei(
            self.w3.eth.get_balance(self.config.ADDRESS_SENDER), "ether"
        )
        new_balance: float = balance
        while True:
            new_balance = self.w3.from_wei(
                self.w3.eth.get_balance(self.config.ADDRESS_SENDER), "ether"
            )
            if new_balance != balance:
                log(log.INFO, "Balance changed: %s %s", new_balance, self.coin)

                diff: float = new_balance - balance
                if diff > 0:
                    log(log.INFO, "Received: %s %s", diff, Units.gmee.value)
                    self.send_transaction(
                        address_receiver=self.config.ADDRESS_RECEIVER,
                        value=diff,
                        coin=Units.gmee.value,
                    )
                else:
                    log(log.INFO, "Sent: %s %s", abs(diff), self.coin)

                balance = new_balance
            else:
                log(log.INFO, "Balance not changed: %s %s", new_balance, self.coin)
            time.sleep(2)
