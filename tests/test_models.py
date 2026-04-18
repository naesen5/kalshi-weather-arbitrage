"""Tests for Kalshi models."""

import pytest
from kalshi_weather_arb.models import (
    Market,
    Orderbook,
    Order,
    Position,
    MarketType,
    DryRunError,
)


class TestMarket:
    """Tests for Market dataclass."""

    def test_market_from_api_response(self):
        """Market parses correctly from Kalshi API response."""
        api_data = {
            "ticker": "KLSHI-TEMP-NYC-90",
            "title": "Will NYC reach 90°F today?",
            "status": "open",
            "category": "weather",
            "yes_bid": 45,
            "yes_ask": 47,
            "no_bid": 53,
            "no_ask": 55,
            "last_price": 46,
            "volume": 12345,
            "open_interest": 67890,
        }
        market = Market.from_api(api_data)
        assert market.ticker == "KLSHI-TEMP-NYC-90"
        assert market.title == "Will NYC reach 90°F today?"
        assert market.status == "open"
        assert market.category == "weather"
        assert market.yes_bid == 45
        assert market.yes_ask == 47
        assert market.last_price == 46

    def test_market_implied_probability(self):
        """Market calculates implied probability correctly."""
        api_data = {
            "ticker": "TEST",
            "title": "Test",
            "status": "open",
            "category": "weather",
            "yes_bid": 30,
            "yes_ask": 35,
            "no_bid": 65,
            "no_ask": 70,
            "last_price": 33,
            "volume": 0,
            "open_interest": 0,
        }
        market = Market.from_api(api_data)
        # Implied prob = last_price / 100
        assert market.implied_probability == 0.33

    def test_market_type_temperature_high(self):
        """MarketType enum includes TEMPERATURE_HIGH."""
        assert MarketType.TEMPERATURE_HIGH.value == "temperature_high"

    def test_market_type_temperature_low(self):
        """MarketType enum includes TEMPERATURE_LOW."""
        assert MarketType.TEMPERATURE_LOW.value == "temperature_low"


class TestOrderbook:
    """Tests for Orderbook dataclass."""

    def test_orderbook_from_api_response(self):
        """Orderbook parses correctly from Kalshi API response."""
        api_data = {
            "yes": {"bid": 45, "ask": 47, "bid_size": 100, "ask_size": 200},
            "no": {"bid": 53, "ask": 55, "bid_size": 300, "ask_size": 400},
        }
        orderbook = Orderbook.from_api(api_data)
        assert orderbook.yes_bid == 45
        assert orderbook.yes_ask == 47
        assert orderbook.no_bid == 53
        assert orderbook.no_ask == 55
        assert orderbook.yes_bid_size == 100
        assert orderbook.yes_ask_size == 200

    def test_orderbook_best_price(self):
        """Orderbook returns best YES price."""
        api_data = {
            "yes": {"bid": 45, "ask": 47, "bid_size": 100, "ask_size": 200},
            "no": {"bid": 53, "ask": 55, "bid_size": 300, "ask_size": 400},
        }
        orderbook = Orderbook.from_api(api_data)
        assert orderbook.best_yes_price == 45  # bid
        assert orderbook.best_no_price == 53   # bid


class TestOrder:
    """Tests for Order dataclass."""

    def test_order_from_api_response(self):
        """Order parses correctly from Kalshi API response."""
        api_data = {
            "order_id": "12345",
            "ticker": "KLSHI-TEMP-NYC-90",
            "side": "yes",
            "count": 100,
            "price": 45,
            "status": "open",
            "created_time": "2026-04-18T03:00:00Z",
        }
        order = Order.from_api(api_data)
        assert order.order_id == "12345"
        assert order.ticker == "KLSHI-TEMP-NYC-90"
        assert order.side == "yes"
        assert order.count == 100
        assert order.price == 45
        assert order.status == "open"

    def test_order_total_value(self):
        """Order calculates total value correctly."""
        api_data = {
            "order_id": "12345",
            "ticker": "KLSHI-TEMP-NYC-90",
            "side": "yes",
            "count": 100,
            "price": 45,
            "status": "open",
            "created_time": "2026-04-18T03:00:00Z",
        }
        order = Order.from_api(api_data)
        # Total value = count * price
        assert order.total_value == 4500  # 100 * 45


class TestPosition:
    """Tests for Position dataclass."""

    def test_position_from_api_response(self):
        """Position parses correctly from Kalshi API response."""
        api_data = {
            "ticker": "KLSHI-TEMP-NYC-90",
            "side": "yes",
            "count": 500,
            "avg_price": 42,
            "realized_pnl": 150,
        }
        position = Position.from_api(api_data)
        assert position.ticker == "KLSHI-TEMP-NYC-90"
        assert position.side == "yes"
        assert position.count == 500
        assert position.avg_price == 42
        assert position.realized_pnl == 150

    def test_position_unrealized_pnl(self):
        """Position calculates unrealized P&L correctly."""
        position = Position(
            ticker="KLSHI-TEMP-NYC-90",
            side="yes",
            count=500,
            avg_price=42,
            realized_pnl=150,
        )
        # Unrealized P&L = count * (current_price - avg_price)
        # If current price is 45: 500 * (45 - 42) = 1500
        assert position.unrealized_pnl(current_price=45) == 1500

    def test_position_total_pnl(self):
        """Position calculates total P&L correctly."""
        position = Position(
            ticker="KLSHI-TEMP-NYC-90",
            side="yes",
            count=500,
            avg_price=42,
            realized_pnl=150,
        )
        # Total P&L = realized + unrealized
        assert position.total_pnl(current_price=45) == 1650  # 150 + 1500


class TestDryRunError:
    """Tests for DryRunError exception."""

    def test_dry_run_error_is_exception(self):
        """DryRunError is a valid exception."""
        with pytest.raises(DryRunError):
            raise DryRunError("Dry run mode enabled")

    def test_dry_run_error_message(self):
        """DryRunError carries message."""
        msg = "Dry run mode enabled"
        try:
            raise DryRunError(msg)
        except DryRunError as e:
            assert str(e) == msg
