"""Dashboard display — terminal UI using rich.live."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box


class Dashboard:
    """Dashboard — live terminal view using rich.live."""

    MIN_EDGE_GOOD = 5.0
    MIN_EDGE_BORDERLINE = 0.0

    def __init__(self, dry_run: bool = False, update_interval: float = 30.0):
        self.dry_run = dry_run
        self.update_interval = update_interval
        self.console = Console()
        self.live = Live(self.console)

    def start(self) -> None:
        """Start the live display."""
        self.live.start()

    def stop(self) -> None:
        """Stop the live display."""
        self.live.stop()

    def _format_edge(self, edge: float) -> Text:
        """Format edge value with color coding."""
        if edge >= self.MIN_EDGE_GOOD:
            return Text(f"{edge:+.1f}%", style="green")
        elif edge >= self.MIN_EDGE_BORDERLINE:
            return Text(f"{edge:+.1f}%", style="yellow")
        else:
            return Text(f"{edge:+.1f}%", style="red")

    def _format_checkmark(self, edge: float) -> Text:
        """Format checkmark based on edge value."""
        if edge >= self.MIN_EDGE_BORDERLINE:
            return Text("✓", style="green")
        else:
            return Text("✗", style="red")

    def render_scan_results(self, results: List[Dict[str, Any]]) -> Table:
        """Render scan results as a rich table."""
        table = Table(
            title="Current Scan",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("Market", style="magenta")
        table.add_column("Station", style="cyan")
        table.add_column("Obs Age", style="white")
        table.add_column("Curr °F", style="white")
        table.add_column("Threshold", style="white")
        table.add_column("Model%", style="yellow")
        table.add_column("Market%", style="yellow")
        table.add_column("Edge", style="white")
        table.add_column("", style="white")

        for r in results:
            market = r.get("market", "Unknown")
            station = r.get("station", "N/A")
            obs_age = r.get("obs_age", "N/A")
            curr_temp = r.get("curr_temp", "N/A")
            threshold = r.get("threshold", "N/A")
            model_prob = r.get("model_prob", 0)
            market_prob = r.get("market_prob", 0)
            edge = r.get("edge", 0)

            table.add_row(
                str(market),
                str(station),
                str(obs_age),
                f"{curr_temp:.1f}",
                f"{threshold:.1f}",
                f"{model_prob:.0f}%",
                f"{market_prob:.0f}%",
                self._format_edge(edge),
                self._format_checkmark(edge),
            )

        return table

    def render_open_positions(self, positions: List[Dict[str, Any]]) -> Panel:
        """Render open positions as a rich panel."""
        if not positions:
            return Panel(
                "[dim]No open positions[/dim]", title="Open Positions", box=box.ROUNDED
            )

        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("Ticker", style="magenta")
        table.add_column("Entry Price", style="white")
        table.add_column("Curr Price", style="white")
        table.add_column("Unrealised P&L", style="white")
        table.add_column("Model Prob", style="yellow")

        for p in positions:
            table.add_row(
                str(p.get("ticker", "N/A")),
                f"${p.get('entry_price', 0):.2f}",
                f"${p.get('current_price', 0):.2f}",
                f"${p.get('unrealised_pl', 0):.2f}",
                f"{p.get('model_prob', 0):.0f}%",
            )

        return Panel(table, title="Open Positions", box=box.ROUNDED)

    def render_recent_trades(self, ledger: List[Dict[str, Any]]) -> Panel:
        """Render recent trades (last 10) as a rich panel."""
        if not ledger:
            return Panel(
                "[dim]No trades yet[/dim]", title="Recent Trades", box=box.ROUNDED
            )

        recent = ledger[-10:]
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("Time", style="white")
        table.add_column("Contract", style="cyan")
        table.add_column("Amount", style="white")
        table.add_column("Profit", style="white")
        table.add_column("Result", style="white")

        for entry in recent:
            timestamp = entry.get("timestamp", "N/A")[:16]  # truncate to HH:MM
            contract_id = entry.get("contract_id", "N/A")
            amount = entry.get("amount", 0)
            profit = entry.get("profit", 0)
            win = entry.get("win", False)
            result = "WIN" if win else "LOSS"

            style = "green" if win else "red"
            table.add_row(
                timestamp,
                str(contract_id),
                f"${amount:.2f}",
                f"${profit:.2f}",
                Text(result, style=style),
            )

        return Panel(table, title="Recent Trades", box=box.ROUNDED)

    def render_system_status(
        self,
        last_scan_time: Optional[datetime],
        next_scan_seconds: Optional[int],
        balance: Optional[float] = None,
        daily_pl: Optional[float] = None,
        daily_exposure_used: Optional[float] = None,
        daily_exposure_max: Optional[float] = None,
    ) -> Panel:
        """Render system status as a rich panel."""
        mode_text = "DRY RUN" if self.dry_run else "LIVE"
        mode_style = "yellow" if self.dry_run else "red bold"
        mode = Text(mode_text, style=mode_style)

        lines = [f"[bold]Mode:[/bold] {mode}"]

        if last_scan_time:
            lines.append(
                f"[bold]Last Scan:[/bold] {last_scan_time.strftime('%H:%M:%S')}"
            )

        if next_scan_seconds is not None:
            lines.append(f"[bold]Next Scan:[/bold] in {next_scan_seconds}s")

        if balance is not None:
            lines.append(f"[bold]Balance:[/bold] ${balance:.2f}")

        if daily_pl is not None:
            lines.append(f"[bold]Daily P&L:[/bold] ${daily_pl:+.2f}")

        if daily_exposure_used is not None and daily_exposure_max is not None:
            pct = (
                (daily_exposure_used / daily_exposure_max * 100)
                if daily_exposure_max > 0
                else 0
            )
            lines.append(
                f"[bold]Daily Exposure:[/bold] ${daily_exposure_used:.0f}/"
                f"{daily_exposure_max:.0f} "
                f"({pct:.0f}%)"
            )

        return Panel("\n".join(lines), title="System Status", box=box.ROUNDED)

    def update(
        self,
        scan_results: Optional[List[Dict[str, Any]]] = None,
        open_positions: Optional[List[Dict[str, Any]]] = None,
        ledger: Optional[List[Dict[str, Any]]] = None,
        last_scan_time: Optional[datetime] = None,
        next_scan_seconds: Optional[int] = None,
        balance: Optional[float] = None,
        daily_pl: Optional[float] = None,
        daily_exposure_used: Optional[float] = None,
        daily_exposure_max: Optional[float] = None,
    ) -> None:
        """Update the dashboard with new data."""
        from rich.console import NewLine

        self.live.update(
            self.render_system_status(
                last_scan_time,
                next_scan_seconds,
                balance,
                daily_pl,
                daily_exposure_used,
                daily_exposure_max,
            ),
            NewLine(),
            self.render_scan_results(scan_results or []),
            NewLine(),
            self.render_open_positions(open_positions or []),
            NewLine(),
            self.render_recent_trades(ledger or []),
        )
