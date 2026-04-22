"""Data models for Kalshi API."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MarketType(Enum):
    """Market type categories."""

    TEMPERATURE_HIGH = "temperature_high"
    TEMPERATURE_LOW = "temperature_low"
    OTHER = "other"


class DryRunError(Exception):
    """Raised when an operation is attempted in dry-run mode."""

    pass


@dataclass
class Market:
    """
    Represents a Kalshi market.

    Attributes:
        ticker: Market ticker symbol (e.g., 'KLSHI-TEMP-NYC-90')
        title: Market title/description
        status: Market status ('open', 'closed', 'resolved')
        category: Market category (e.g., 'weather', 'politics')
        yes_bid: Best YES bid price in cents
        yes_ask: Best YES ask price in cents
        no_bid: Best NO bid price in cents
        no_ask: Best NO ask price in cents
        last_price: Last traded price in cents
        volume: Total volume traded
        open_interest: Total contracts outstanding
    """

    ticker: str
    title: str
    status: str
    category: str
    yes_bid: int
    yes_ask: int
    no_bid: int
    no_ask: int
    last_price: int
    volume: int
    open_interest: int

    @classmethod
    def from_api(cls, data: dict) -> "Market":
        """Create Market from API response."""
        return cls(
            ticker=data["ticker"],
            title=data["title"],
            status=data["status"],
            category=data["category"],
            yes_bid=data["yes_bid"],
            yes_ask=data["yes_ask"],
            no_bid=data["no_bid"],
            no_ask=data["no_ask"],
            last_price=data["last_price"],
            volume=data.get("volume", 0),
            open_interest=data.get("open_interest", 0),
        )

    @property
    def implied_probability(self) -> float:
        """Market's implied probability (YES price / 100)."""
        return self.last_price / 100.0

    @property
    def mid_price(self) -> float:
        """Mid price between bid and ask."""
        return (self.yes_bid + self.yes_ask) / 2.0


@dataclass
class Orderbook:
    """
    Represents the orderbook for a market.

    Attributes:
        yes_bid: Best YES bid price in cents
        yes_ask: Best YES ask price in cents
        yes_bid_size: Size available at yes_bid
        yes_ask_size: Size available at yes_ask
        no_bid: Best NO bid price in cents
        no_ask: Best NO ask price in cents
        no_bid_size: Size available at no_bid
        no_ask_size: Size available at no_ask
    """

    yes_bid: int
    yes_ask: int
    yes_bid_size: int
    yes_ask_size: int
    no_bid: int
    no_ask: int
    no_bid_size: int
    no_ask_size: int

    @classmethod
    def from_api(cls, data: dict) -> "Orderbook":
        """Create Orderbook from API response."""
        return cls(
            yes_bid=data["yes"]["bid"],
            yes_ask=data["yes"]["ask"],
            yes_bid_size=data["yes"]["bid_size"],
            yes_ask_size=data["yes"]["ask_size"],
            no_bid=data["no"]["bid"],
            no_ask=data["no"]["ask"],
            no_bid_size=data["no"]["bid_size"],
            no_ask_size=data["no"]["ask_size"],
        )

    @property
    def best_yes_price(self) -> int:
        """Best price to buy YES (the bid)."""
        return self.yes_bid

    @property
    def best_no_price(self) -> int:
        """Best price to buy NO (the bid)."""
        return self.no_bid


@dataclass
class Order:
    """
    Represents a Kalshi order.

    Attributes:
        order_id: Unique order identifier
        ticker: Market ticker
        side: 'yes' or 'no'
        count: Number of contracts
        price: Price per contract in cents
        status: Order status ('open', 'filled', 'cancelled', 'expired')
        created_time: ISO timestamp when order was created
    """

    order_id: str
    ticker: str
    side: str
    count: int
    price: int
    status: str
    created_time: str

    @classmethod
    def from_api(cls, data: dict) -> "Order":
        """Create Order from API response."""
        return cls(
            order_id=data["order_id"],
            ticker=data["ticker"],
            side=data["side"],
            count=data["count"],
            price=data["price"],
            status=data["status"],
            created_time=data["created_time"],
        )

    @property
    def total_value(self) -> int:
        """Total value in cents (count * price)."""
        return self.count * self.price


@dataclass
class Position:
    """
    Represents a position in a market.

    Attributes:
        ticker: Market ticker
        side: 'yes' or 'no'
        count: Number of contracts held
        avg_price: Average entry price in cents
        realized_pnl: Realized P&L in cents
    """

    ticker: str
    side: str
    count: int
    avg_price: int
    realized_pnl: int

    @classmethod
    def from_api(cls, data: dict) -> "Position":
        """Create Position from API response."""
        return cls(
            ticker=data["ticker"],
            side=data["side"],
            count=data["count"],
            avg_price=data["avg_price"],
            realized_pnl=data.get("realized_pnl", 0),
        )

    def unrealized_pnl(self, current_price: int) -> int:
        """
        Calculate unrealized P&L in cents.

        Args:
            current_price: Current market price in cents

        Returns:
            Unrealized P&L (positive if profitable)
        """
        if self.side == "yes":
            return self.count * (current_price - self.avg_price)
        else:  # no side
            return self.count * (self.avg_price - current_price)

    def total_pnl(self, current_price: int) -> int:
        """
        Calculate total P&L (realized + unrealized).

        Args:
            current_price: Current market price in cents

        Returns:
            Total P&L in cents
        """
        return self.realized_pnl + self.unrealized_pnl(current_price)


@dataclass
class Opportunity:
    """
    Represents an arbitrage opportunity.

    Attributes:
        market_ticker: Kalshi market ticker symbol
        market_title: Market title
        station: ICAO station code
        current_temp_f: Current temperature in Fahrenheit
        obs_age_minutes: Age of METAR observation in minutes
        threshold_f: Temperature threshold in Fahrenheit
        model_probability: Model-calculated probability
        market_probability: Market implied probability
        edge: Difference (model - market)
        ask_price_cents: Ask price in cents
        recommended_side: 'yes' or 'no'
    """

    market_ticker: str
    market_title: str
    station: str
    current_temp_f: float
    obs_age_minutes: float
    threshold_f: float
    model_probability: float
    market_probability: float
    edge: float
    ask_price_cents: int
    recommended_side: str
