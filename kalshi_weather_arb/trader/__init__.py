"""Trader module — auto-trader, ledger, monitor."""

from kalshi_weather_arb.trader.auto_trader import AutoTrader, RiskState, TradeResult
from kalshi_weather_arb.trader.ledger import TradeLedger
from kalshi_weather_arb.trader.monitor import TradeMonitor

# Backward compatibility alias
Trader = AutoTrader

__all__ = ["AutoTrader", "RiskState", "TradeResult", "TradeLedger", "TradeMonitor", "Trader"]
