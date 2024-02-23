from pydantic import BaseModel, ConfigDict
from enum import Enum


class Transaction(BaseModel):
    nonce: int
    to: str
    value: int
    gas: int
    gasPrice: int
    chainId: int | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class Units(Enum):
    eth = "eth"
    gmee = "gmee"
