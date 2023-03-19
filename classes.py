from attr import define
from pydantic import BaseModel


@define
class AttrsPrimitives:
    a: bytes
    b: str
    c: int
    d: float
    e: bool


class PydanticPrimitives(BaseModel):
    a: bytes
    b: str
    c: int
    d: float
    e: bool

a = AttrsPrimitives(a=b'hello', b='hello', c=1, d=10.2, e=True)
p = PydanticPrimitives(a=b'hello', b='hello', c=1, d=10.2, e=True)


@define
class AttrsPrimitives2:
    a: Optional[bytes]
    b: Optional[str]
    c: Optional[int]
    d: Optional[float]
    e: bool


class PydanticPrimitives2(BaseModel):
    a: Optional[bytes]
    b: Optional[str]
    c: Optional[int]
    d: Optional[float]
    e: bool