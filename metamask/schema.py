from pydantic import BaseModel, ConfigDict


class Transaction(BaseModel):
    nonce: int
    to: str
    value: int
    gas: int
    gasPrice: int
    chainId: int

    model_config = ConfigDict(
        from_attributes=True,
    )
