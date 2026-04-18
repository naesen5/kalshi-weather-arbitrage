"""Backtest engine — replay historical data and simulate bets."""

from typing import Any, Dict, List, Optional

from kalshi_weather_arb.backtest.data_loader import KalshiPriceLoader, METARLoader
from kalshi_weather_arb.probability_model import TemperatureProbModel


class Backtester:
    """Backtest engine — replay historical data and simulate bets."""

    MIN_EDGE = 5.0

    def __init__(
        self,
        metar_loader: METARLoader,
        price_loader: KalshiPriceLoader,
        model: Optional[TemperatureProbModel] = None,
    ):
        self.metar_loader = metar_loader
        self.price_loader = price_loader
        self.model = model or TemperatureProbModel()
        self.results: List[Dict[str, Any]] = []

    def run_backtest(
        self,
        station: str,
        ticker: str,
        start_date: str,
        end_date: str,
        bet_amount: float = 100.0,
    ) -> Dict[str, Any]:
        """Run backtest on historical data."""
        metar_data = self.metar_loader.load_metar_history(station, start_date, end_date)
        price_data = self.price_loader.load_kalshi_price_history(ticker)

        total_profit = 0.0
        wins = 0
        trades = 0

        for obs in metar_data:
            # Find matching price
            price = self._find_matching_price(price_data, obs["timestamp"])
            if price is None:
                continue

            # Calculate probability
            prob = self.model.p_exceed(
                current_temp_f=obs["temp_f"],
                dewpoint_f=40.0,
                hour_of_day=12.0,
                threshold_f=50.0,
            )

            # Calculate implied edge
            implied_prob = 1.0 / price
            edge = (prob - implied_prob) * 100

            if edge > self.MIN_EDGE:
                # Simulate bet
                trades += 1
                profit = bet_amount * (price - 1) if True else -bet_amount
                total_profit += profit
                wins += 1 if profit > 0 else 0

                self.results.append(
                    {
                        "timestamp": obs["timestamp"],
                        "temp": obs["temp_f"],
                        "price": price,
                        "prob": prob,
                        "edge": edge,
                        "profit": profit,
                        "win": profit > 0,
                    }
                )

        total = len(self.results)
        win_rate = wins / total if total > 0 else 0.0
        avg_edge = sum(r["edge"] for r in self.results) / total if total > 0 else 0.0
        sharpe = (avg_edge / (total_profit / total)) ** 0.5 if total_profit > 0 else 0.0

        return {
            "station": station,
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "total_trades": trades,
            "total_profit": total_profit,
            "win_rate": win_rate,
            "avg_edge": avg_edge,
            "sharpe_ratio": sharpe,
        }

    def _find_matching_price(
        self, prices: List[Dict[str, Any]], timestamp: str
    ) -> Optional[float]:
        """Find matching price for timestamp."""
        for p in prices:
            if p["timestamp"][:10] in timestamp:
                return p["price"]
        return None
