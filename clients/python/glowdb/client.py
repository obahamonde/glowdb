from __future__ import annotations
from types import TracebackType
import typing as tp
from dataclasses import dataclass, field
from uuid import uuid4

import orjson
import websockets
from .models import DocumentObject

O = tp.TypeVar("O", bound=DocumentObject)

@dataclass
class RPCClient(tp.Generic[O]):
    uri: str = field(default="ws://localhost:8888")
    ws: tp.Optional[websockets.WebSocketClientProtocol] = field(default=None)
    model: tp.Type[O] = field(default=DocumentObject)

    async def connect(self):
        self.ws = await websockets.connect(self.uri)

    async def close(self):
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def _send_request(self, method: str, params: dict[str, tp.Any]):
        if not self.ws:
            raise ValueError("Not connected to the server")
        request_id = str(uuid4())
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id,
        }
        await self.ws.send(orjson.dumps(request).decode())
        response_raw = await self.ws.recv()
        response = orjson.loads(response_raw)  # type: ignore
        if "error" in response and response["error"] is not None:
            error = response["error"]
            raise Exception(f"Error {error['code']}: {error['message']}")
        else:
            return response.get("result")

    async def create_table(self, table_name: str):
        params = {"table_name": table_name}
        return await self._send_request("CreateTable", params)

    async def delete_table(self, table_name: str):
        params = {"table_name": table_name}
        return await self._send_request("DeleteTable", params)

    async def put_item(self, table_name: str, item: O):
        params = {"table_name": table_name, "item": item.model_dump()}
        return await self._send_request("PutItem", params)

    async def get_item(self, table_name: str, id: str):
        params = {"table_name": table_name, "id": id}
        result = await self._send_request("GetItem", params)
        return self.model.model_validate(result)

    async def update_item(self, table_name: str, id: str, updates: dict[str, tp.Any]):
        params = {"table_name": table_name, "id": id, "updates": updates}
        return await self._send_request("UpdateItem", params)

    async def delete_item(self, table_name: str, id: str):
        params = {"table_name": table_name, "id": id}
        return await self._send_request("DeleteItem", params)

    async def scan(self, table_name: str, limit: int = 25, offset: int = 0):
        params = {"table_name": table_name, "limit": limit, "offset": offset}
        result = await self._send_request("Scan", params)
        return [self.model.model_validate(item) for item in result]

    async def query(
        self,
        table_name: str,
        filters: dict[str, tp.Any] | None = None,
        limit: int = 25,
        offset: int = 0,
    ):
        params = {"table_name": table_name, "limit": limit, "offset": offset}
        if filters:
            params["filters"] = filters  # type: ignore
        result = await self._send_request("Query", params)
        return [self.model.model_validate(item) for item in result]

    async def batch_get_item(self, ids: tp.List[str], table_name: str):
        params = {"table_name": table_name, "ids": ids}
        result = await self._send_request("BatchGetItem", params)
        return [self.model.model_validate(item) for item in result]

    async def batch_write_item(self, items: tp.List[O], table_name: str):
        items_data = [item.model_dump() for item in items]
        params = {"table_name": table_name, "items": items_data}
        return await self._send_request("BatchWriteItem", params)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type: tp.Optional[BaseException], exc_value: tp.Optional[BaseException], traceback: tp.Optional[TracebackType]):
        await self.close()
