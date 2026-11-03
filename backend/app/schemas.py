
from typing import Literal

from pydantic import BaseModel, Field


class ActionRequest(BaseModel):
    action: Literal[
        "read_demo_records",
        "delete_customer_records",
    ]

    approval_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )


class AIRequest(BaseModel):
    user_message: str = Field(
        min_length=1,
        max_length=1000,
    )
