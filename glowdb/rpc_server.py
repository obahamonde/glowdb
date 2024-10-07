import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union

import click
import orjson
import websockets
from pydantic import BaseModel, ValidationError
from websockets.server import WebSocketServerProtocol

from .models import DocumentObject, GlowMethod
from .utils import get_logger

logger = get_logger(__name__)

# Type Aliases
DataObject = Union[
    Dict[str, Any],
    List[Dict[str, Any]],
    str,
    int,
    float,
    bool,
    DocumentObject,
    List[DocumentObject],
]


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

    model_config = {
        "json_encoders": {DocumentObject: lambda v: v.model_dump()},
        "arbitrary_types_allowed": True,
    }


class RPCError(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data


# RPC Server Class
class RPCServer:
    def __init__(self):
        self.methods: Dict[
            GlowMethod, Callable[[Dict[str, Any]], Coroutine[Any, Any, DataObject]]
        ] = {
            "CreateTable": self.create_table,
            "DeleteTable": self.delete_table,
            "GetItem": self.get_item,
            "PutItem": self.put_item,
            "UpdateItem": self.update_item,
            "DeleteItem": self.delete_item,
            "Scan": self.scan,
            "Query": self.query,
            "BatchGetItem": self.batch_get_item,
            "BatchWriteItem": self.batch_write_item,
        }

    async def create_table(self, params: Dict[str, Any]) -> Dict[str, str]:
        table_name = params["table_name"]
        return await DocumentObject.create_table(table_name)

    async def delete_table(self, params: Dict[str, Any]) -> Dict[str, str]:
        table_name = params["table_name"]
        return await DocumentObject.delete_table(table_name)

    async def get_item(self, params: Dict[str, Any]) -> DocumentObject:
        table_name = params["table_name"]
        item_id = params["id"]
        return await DocumentObject.get_item(table_name, item_id)

    async def put_item(self, params: Dict[str, Any]) -> DocumentObject:
        table_name = params["table_name"]
        data = params["item"]
        item = DocumentObject(**data)
        return await item.put_item(table_name)

    async def update_item(self, params: Dict[str, Any]) -> DocumentObject:
        table_name = params["table_name"]
        item_id = params["id"]
        updates = params["updates"]
        return await DocumentObject.update_item(table_name, item_id, updates)

    async def delete_item(self, params: Dict[str, Any]) -> Dict[str, str]:
        table_name = params["table_name"]
        item_id = params["id"]
        return await DocumentObject.delete_item(table_name, item_id)

    async def scan(self, params: Dict[str, Any]) -> List[DocumentObject]:
        table_name = params["table_name"]
        limit = params.get("limit", 25)
        offset = params.get("offset", 0)
        return await DocumentObject.query(table_name, limit=limit, offset=offset)

    async def query(self, params: Dict[str, Any]) -> List[DocumentObject]:
        table_name = params["table_name"]
        filters = params.get("filters")
        limit = params.get("limit", 25)
        offset = params.get("offset", 0)
        return await DocumentObject.query(table_name, filters, limit, offset)

    async def batch_get_item(self, params: Dict[str, Any]) -> List[DocumentObject]:
        table_name = params["table_name"]
        ids = params["ids"]
        return await DocumentObject.batch_get_item(table_name, ids)

    async def batch_write_item(self, params: Dict[str, Any]) -> List[DocumentObject]:
        table_name = params["table_name"]
        items_data = params["items"]
        items = [DocumentObject(**data) for data in items_data]
        return await DocumentObject.batch_write_item(table_name, items)

    async def handle_request(self, websocket: WebSocketServerProtocol, path: str):
        while True:
            try:
                message = await websocket.recv()
                logger.info(f"Received message: {message}")
                request_data = orjson.loads(message)

                try:
                    request = RPCRequest(**request_data)
                    logger.info(f"Handling method: {request.method}")

                    if request.method not in self.methods:
                        raise RPCError(-32601, f"Method '{request.method}' not found")

                    result = await self.methods[request.method](request.params)
                    response = RPCResponse(result=result, id=request.id)

                except ValidationError as e:
                    response = RPCResponse(
                        error={"code": -32602, "message": str(e)},
                        id=request_data.get("id", ""),
                    )
                except RPCError as e:
                    response = RPCResponse(
                        error={"code": e.code, "message": e.message, "data": e.data},
                        id=request_data.get("id", ""),
                    )
                except Exception as e:
                    logger.error(f"Unexpected error: {str(e)}")
                    response = RPCResponse(
                        error={"code": -32000, "message": str(e)},
                        id=request_data.get("id", ""),
                    )

                response_json = orjson.dumps(response.model_dump()).decode()
                logger.info(f"Sending response: {response_json}")
                await websocket.send(response_json)

            except websockets.exceptions.ConnectionClosed:
                logger.info("WebSocket connection closed")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                break

        logger.info("Exiting session")

    def run(self, host: str = "0.0.0.0", port: int = 8888):
        logger.info(f"Starting RPC server on {host}:{port}")
        start_server = websockets.serve(self.handle_request, host, port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()


@click.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8888)
def run(host: str = "0.0.0.0", port: int = 8888):
    """
    Runs the RPC server.

    Args:
        host (str): The host address to bind the server to. Defaults to "0.0.0.0".
        port (int): The port number to bind the server to. Defaults to 8888.
    """
    server = RPCServer()
    server.run(host, port)
