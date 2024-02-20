import json

import websocket
from web3 import Web3
from web3.exceptions import TransactionNotFound
from web3.middleware import geth_poa_middleware
from web3.types import ENS

from metamask.config import Config, get_config
from metamask.logger import log

CFG: Config = get_config()

address: ENS = CFG.ADDRESS_SENDER
gmee_contract_address: ENS = CFG.GMEE_ADDRESS_SENDER

w3: Web3 = Web3(Web3.HTTPProvider(CFG.LINEA_NETWORK))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


def on_message(ws, message):
    message = json.loads(message)
    if "params" in message and "result" in message["params"]:
        result = message["params"]["result"]
        try:
            tx = w3.eth.get_transaction(result["hash"])
        except TransactionNotFound:
            log(log.INFO, "Transaction not found - %s", result)
            return
        log(log.INFO, "Found new block - %s", tx)
        if "topics" in result and result["topics"][1]:
            sender_address = Web3.to_checksum_address(result["topics"][1][-40:])

            if sender_address == address:
                log(log.INFO, "Found new transaction - %s", address)
                log(log.INFO, "Transaction details - %s", result)
                # Implement next transaction processing here


def on_error(ws: websocket.WebSocket, error):
    log(log.ERROR, error)


def on_close(ws: websocket.WebSocket, close_status_code, close_msg):
    log(log.CRITICAL, "WebSocket closed")


def on_open(ws):
    log(log.INFO, "WebSocket opened")

    subscription_request = {
        "id": 1,
        "method": "eth_subscribe",
        "params": [
            "logs",
            {
                "address": CFG.ADDRESS_SENDER,
                "topics": [],
            },
        ],
    }
    ws.send(json.dumps(subscription_request))


if __name__ == "__main__":
    websocket.enableTrace(True)

    ws = websocket.WebSocketApp(
        CFG.INFURA_NETWORK_WSS,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )

    ws.run_forever()
