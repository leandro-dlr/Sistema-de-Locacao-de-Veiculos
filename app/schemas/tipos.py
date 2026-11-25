from decimal import Decimal
from typing import Annotated

from pydantic import Field, PlainSerializer

Dinheiro = Annotated[
    Decimal,
    Field(max_digits=10, decimal_places=2),
    PlainSerializer(lambda v: float(v), return_type=float, when_used="json"),
]
