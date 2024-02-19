import json

import websocket
from web3 import Web3
from web3.types import ENS

from config import Config, get_config
from logger import log

CFG: Config = get_config()

address: ENS = CFG.ADDRESS_SENDER


def on_message(ws, message):
    message = json.loads(message)
    if "params" in message and "result" in message["params"]:
        result = message["params"]["result"]
        if "topics" in result and result["topics"][1]:
            sender_address = Web3.to_checksum_address(result["topics"][1][-40:])
            if sender_address == address:
                log(log.INFO, "Found new transaction - %s", address)
                log(log.INFO, "Transaction details - %s", result)
                # Implement next transaction processing here


def on_error(ws, error):
    log(log.ERROR, error)


def on_close(ws, **kwargs):
    log(log.CRITICAL, "WebSocket closed")


def on_open(ws):
    log(log.INFO, "WebSocket opened")

    subscription_request = {
        "id": 1,
        "method": "eth_subscribe",
        "params": ["newHeads", {}],
    }
    ws.send(json.dumps(subscription_request))

    subscription_request = {
        "id": 2,
        "method": "eth_subscribe",
        "params": ["logs", {"address": address, "topics": []}],
    }
    ws.send(json.dumps(subscription_request))


if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(
        f"wss://mainnet.infura.io/ws/v3/{CFG.INFURA_PROJECT_ID}",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )

    ws.run_forever()
