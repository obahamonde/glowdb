import asyncio
from typing import Literal
from glowdb import RPCClient, DocumentObject


class Message(DocumentObject):
    role: Literal["user", "assistant", "system"]
    content: str
    



async def main():
	async with RPCClient[Message]() as client:
		await client.create_table("messages")
		await client.put_item("messages", Message(role="system", content="You are a helpful assistant"))
		await client.scan("messages")

if __name__ == "__main__":
	asyncio.run(main())
 