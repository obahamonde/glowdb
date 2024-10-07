from __future__ import annotations
from typing import Any, Dict, Optional, Literal
from pydantic import BaseModel, Field, computed_field
from functools import cached_property
import uuid
import base64c # type: ignore
# Base Document Model

GlowMethod = Literal[
    "CreateTable",
    "DeleteTable",
    "GetItem",
    "PutItem",
    "UpdateItem",
    "DeleteItem",
    "Scan",
    "Query",
    "BatchGetItem",
    "BatchWriteItem",
]
class DocumentObject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_config = {
        "json_encoders": {bytes: lambda v: base64c.b64encode(v).decode("utf-8")},  # type: ignore
        "arbitrary_types_allowed": True,
    }

    @computed_field(return_type=str)
    @cached_property
    def object(self) -> str:
        return self.__class__.__name__.lower()



# RPC Request and Response Models
class RPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: GlowMethod
    params: Dict[str, Any]
    id: str


class RPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: str