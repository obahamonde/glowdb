import unittest
from unittest.mock import MagicMock, patch
from glowdb import RPCClient, DocumentObject, RPCRequest, RPCResponse

class TestDocument(DocumentObject):
    content: str


class TestClient(unittest.TestCase):
    def setUp(self):
        self.client = RPCClient[TestDocument](model=TestDocument, uri="ws://test.com")

    @patch("websockets.connect")
    async def test_connect(self, mock_connect: MagicMock):
        mock_ws = MagicMock()
        mock_connect.return_value = mock_ws

        await self.client.connect()

        mock_connect.assert_called_once_with("ws://test.com")
        self.assertEqual(self.client.ws, mock_ws)

    async def test_close(self):
        self.client.ws = MagicMock()
        await self.client.close()
        self.client.ws.close.assert_called_once()
        self.assertIsNone(self.client.ws)

    @patch.object(RPCClient, "request")
    async def test_get_item(self, mock_request):
        mock_request.return_value = RPCResponse(result={"id": "1", "content": "test"})
        result = await self.client.get_item("test_store", "1")
        mock_request.assert_called_once_with(
            RPCRequest(
                method="GetItem", params={"table_name": "test_store", "id": "1"}
            )
        )
        self.assertIsInstance(result, TestDocument)
        self.assertEqual(result.id, "1")
        self.assertEqual(result.content, "test")

    @patch.object(RPCClient, "request")
    async def test_create_table(self, mock_request):
        await self.client.create_table("test_store")
        mock_request.assert_called_once_with(
            RPCRequest(method="CreateTable", params={"table_name": "test_store"})
        )

    @patch.object(RPCClient, "request")
    async def test_scan(self, mock_request):
        mock_request.return_value = RPCResponse(
            result=[{"id": "1", "content": "test1"}, {"id": "2", "content": "test2"}]
        )
        result = await self.client.scan("test_store")
        mock_request.assert_called_once_with(
            RPCRequest(method="Scan", params={"table_name": "test_store"})
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], TestDocument)
        self.assertEqual(result[0].id, "1")
        self.assertEqual(result[0].content, "test1")

    @patch.object(RPCClient, "request")
    async def test_query(self, mock_request):
        mock_request.return_value = RPCResponse(
            result=[{"id": "1", "content": "test1"}]
        )
        result = await self.client.query(
            "test_store", limit=1, offset=0, content="test"
        )
        mock_request.assert_called_once_with(
            RPCRequest(
                method="Query",
                params={
                    "table_name": "test_store",
                    "limit": 1,
                    "offset": 0,
                    "content": "test",
                },
            )
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], TestDocument)
        self.assertEqual(result[0].id, "1")
        self.assertEqual(result[0].content, "test1")

    @patch.object(RPCClient, "request")
    async def test_delete_item(self, mock_request):
        await self.client.delete_item("test_store", "1")
        mock_request.assert_called_once_with(
            RPCRequest(
                method="DeleteItem", params={"table_name": "test_store", "id": "1"}
            )
        )

    @patch.object(RPCClient, "request")
    async def test_update_table(self, mock_request):
        await self.client.update_table("test_store", "new_name")
        mock_request.assert_called_once_with(
            RPCRequest(
                method="UpdateTable",
                params={"table_name": "test_store", "name": "new_name"},
            )
        )

    @patch.object(RPCClient, "request")
    async def test_put_item(self, mock_request):
        doc = TestDocument(id="1", content="test")
        mock_request.return_value = RPCResponse(result={"id": "1", "content": "test"})
        result = await self.client.put_item("test_store", doc)
        mock_request.assert_called_once_with(
            RPCRequest(
                method="PutItem",
                params={
                    "table_name": "test_store",
                    "document": {"id": "1", "content": "test"},
                },
            )
        )
        self.assertIsInstance(result, TestDocument)
        self.assertEqual(result.id, "1")
        self.assertEqual(result.content, "test")

    @patch.object(RPCClient, "request")
    async def test_update_item(self, mock_request):
        mock_request.return_value = RPCResponse(
            result={"id": "1", "content": "updated"}
        )
        result = await self.client.update_item("test_store", "1", content="updated")
        mock_request.assert_called_once_with(
            RPCRequest(
                method="UpdateItem",
                params={
                    "table_name": "test_store",
                    "id": "1",
                    "content": "updated",
                },
            )
        )
        self.assertIsInstance(result, TestDocument)
        self.assertEqual(result.id, "1")
        self.assertEqual(result.content, "updated")



if __name__ == "__main__":
    unittest.main()