import asyncio
import json
import unittest
from unittest.mock import AsyncMock, patch
import websockets

from olymptrade_ws.core.client import OlympTradeClient
from olymptrade_ws.olympconfig import parameters


class MockWebSocket:
    def __init__(self):
        self.state = websockets.State.OPEN
        self.closed = False
        self.recv_queue = asyncio.Queue()
        self.sent_messages = []

    async def recv(self):
        try:
            return await self.recv_queue.get()
        except asyncio.CancelledError:
            raise

    async def send(self, message):
        self.sent_messages.append(message)

    async def close(self):
        self.state = websockets.State.CLOSED
        self.closed = True


class TestOlympTradeClientMocked(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_ws = MockWebSocket()
        self.connect_patcher = patch("websockets.connect", new_callable=AsyncMock)
        self.mock_connect = self.connect_patcher.start()
        self.mock_connect.return_value = self.mock_ws

        self.client = OlympTradeClient(
            access_token="fake_token",
            log_raw_messages=False,
            uri="wss://fake_uri"
        )

    async def asyncTearDown(self):
        if self.client._is_running:
            await self.client.stop()
        self.connect_patcher.stop()

    async def test_client_start_stop(self):
        """Test that the client starts and stops correctly, and background loops run."""
        await self.client.start()
        self.assertTrue(self.client._is_running)
        self.assertTrue(self.client.connection.is_connected)
        self.mock_connect.assert_called_once()

        await self.client.stop()
        self.assertFalse(self.client._is_running)
        self.assertFalse(self.client.connection.is_connected)

    async def test_send_request_with_response(self):
        """Test sending a request and receiving a response matched by UUID."""
        await self.client.start()

        # We need a task to send the request because it waits for a response
        request_task = asyncio.create_task(
            self.client.send_request(event_code=90, data={"test": "data"}, requires_response=True, timeout=2.0)
        )

        # Allow the task to execute and send the message
        await asyncio.sleep(0.1)

        # Check that the request was sent through the mocked WS
        self.assertEqual(len(self.mock_ws.sent_messages), 1)
        sent_msg = json.loads(self.mock_ws.sent_messages[0])[0]
        self.assertEqual(sent_msg["e"], 90)
        self.assertEqual(sent_msg["d"], {"test": "data"})
        uuid_sent = sent_msg["uuid"]

        # Simulate server response with matching UUID
        response_payload = [{"t": 3, "e": 90, "d": {"status": "success"}, "uuid": uuid_sent}]
        await self.mock_ws.recv_queue.put(json.dumps(response_payload))

        # Wait for request to complete and check response
        response = await request_task
        self.assertEqual(response, response_payload[0])

    async def test_event_callback(self):
        """Test registering and triggering callbacks for server pushes."""
        callback_called = asyncio.Event()
        received_msg = None

        async def callback(msg):
            nonlocal received_msg
            received_msg = msg
            callback_called.set()

        self.client.register_callback(parameters.E_TICK_UPDATE, callback)

        await self.client.start()

        # Simulate unsolicited server tick update message
        tick_payload = [{"t": 1, "e": parameters.E_TICK_UPDATE, "d": [{"p": "EURUSD", "q": 1.1023, "t": 1700000000}]}]
        await self.mock_ws.recv_queue.put(json.dumps(tick_payload))

        # Wait for callback to be triggered
        await asyncio.wait_for(callback_called.wait(), timeout=2.0)
        self.assertEqual(received_msg, tick_payload[0])

    async def test_balance_api(self):
        """Test BalanceAPI subscribe and get_last_balance / get_balance."""
        await self.client.start()

        # Mock send_request on client to verify BalanceAPI calls
        self.client.send_request = AsyncMock(return_value={"e": 55, "d": [{"account_id": 123, "group": "demo", "amount": 10000}]})

        # Test subscribe_balance_updates
        await self.client.balance.subscribe_balance_updates()
        self.client.send_request.assert_called_with(98, [[55]], requires_response=False)

        # Test get_last_balance
        self.client._latest_balance = {"e": 55, "d": [{"account_id": 123, "group": "demo", "amount": 10000}]}
        last_bal = self.client.balance.get_last_balance()
        self.assertEqual(last_bal["d"][0]["amount"], 10000)

        # Test get_balance
        self.client.wait_for_balance = AsyncMock(return_value=self.client._latest_balance)
        bal = await self.client.balance.get_balance()
        self.assertEqual(bal["d"][0]["amount"], 10000)

    async def test_market_api_subscribe_ticks(self):
        """Test subscribing and unsubscribing to ticks in MarketAPI."""
        await self.client.start()
        self.client.send_request = AsyncMock()

        await self.client.market.subscribe_ticks("EURUSD")
        self.assertEqual(self.client.send_request.call_count, 2)
        self.client.send_request.assert_any_call(12, [{"pair": "EURUSD"}], requires_response=True)
        self.client.send_request.assert_any_call(280, [{"pair": "EURUSD"}], requires_response=True)

        self.client.send_request.reset_mock()
        await self.client.market.unsubscribe_ticks("EURUSD")
        self.assertEqual(self.client.send_request.call_count, 2)
        self.client.send_request.assert_any_call(13, [{"pair": "EURUSD"}], requires_response=True)
        self.client.send_request.assert_any_call(281, [{"pair": "EURUSD"}], requires_response=True)

    async def test_market_api_get_candles(self):
        """Test retrieving candles from MarketAPI."""
        await self.client.start()
        mock_candles = [{"p": 1.1, "t": 1700000000}]
        self.client.send_request = AsyncMock(return_value={"e": 1003, "d": mock_candles})

        candles = await self.client.market.get_candles("EURUSD", size=60, count=10, end_time=1700000000)
        self.assertEqual(candles, mock_candles)
        self.client.send_request.assert_called_once_with(10, [{"pair": "EURUSD", "size": 60, "to": 1700000000, "solid": True}], requires_response=True)

    async def test_market_api_select_asset(self):
        """Test select_asset which waits for strike updates via callbacks."""
        await self.client.start()

        # Send_request returns confirmation for event 95
        self.client.send_request = AsyncMock(return_value={"e": 95})

        # We trigger the callback manually by simulating the server message
        async def simulate_server_strike_push():
            await asyncio.sleep(0.1)
            # Find the registered callback for e:80 (strike updates) and call it
            self.assertTrue(80 in self.client._event_callbacks)
            callbacks = self.client._event_callbacks[80]
            self.assertEqual(len(callbacks), 1)
            # Call the callback with a mock server message for the pair
            await callbacks[0]({"e": 80, "d": [{"p": "EURUSD", "strike": 1.1234}]})

        asyncio.create_task(simulate_server_strike_push())

        strike_info = await self.client.market.select_asset("EURUSD")
        self.assertIsNotNone(strike_info)
        self.assertEqual(strike_info["strike"], 1.1234)

    async def test_trade_api_place_order(self):
        """Test placing an order in TradeAPI."""
        await self.client.start()
        mock_trade_resp = {"e": 23, "d": [{"id": 999, "status": "opened"}]}
        self.client.send_request = AsyncMock(return_value=mock_trade_resp)

        res = await self.client.trade.place_order(
            pair="EURUSD",
            amount=10,
            direction="up",
            duration=60,
            account_id=123,
            group="demo",
            timestamp=1700000000
        )
        self.assertEqual(res, mock_trade_resp["d"][0])
        self.client.send_request.assert_called_once()
        sent_data = self.client.send_request.call_args[0][1][0]
        self.assertEqual(sent_data["pair"], "EURUSD")
        self.assertEqual(sent_data["amount"], 10)
        self.assertEqual(sent_data["account_id"], 123)
        self.assertEqual(sent_data["group"], "demo")


if __name__ == "__main__":
    unittest.main()
