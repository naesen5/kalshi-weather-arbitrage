"""Backtest report — pretty-print results via rich."""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class BacktestReport:
    """Pretty-print backtest results."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def print_summary(self, results: dict) -> None:
        """Print backtest summary."""
        table = Table(title="Backtest Results", box="ROUNDED")

        table.add_column("Metric", style="bold cyan")
        table.add_column("Value", style="white")

        table.add_row("Station", results.get("station", "N/A"))
        table.add_row("Ticker", results.get("ticker", "N/A"))
        table.add_row("Start Date", results.get("start_date", "N/A"))
        table.add_row("End Date", results.get("end_date", "N/A"))
        table.add_row("Total Trades", str(results.get("total_trades", 0)))
        table.add_row("Total Profit", f"${results.get('total_profit', 0):.2f}")
        table.add_row("Win Rate", f"{results.get('win_rate', 0):.1%}")
        table.add_row("Avg Edge", f"{results.get('avg_edge', 0):.1f}%")
        table.add_row("Sharpe Ratio", f"{results.get('sharpe_ratio', 0):.2f}")

        self.console.print(Panel(table, title="Backtest Summary"))
