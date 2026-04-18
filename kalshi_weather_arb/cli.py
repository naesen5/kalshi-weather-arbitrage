"""CLI — command-line interface for kalshi-weather-arbitrage."""

import argparse

from kalshi_weather_arb.client import KalshiClient
from kalshi_weather_arb.dashboard.display import Dashboard
from kalshi_weather_arb.scanner import ArbitrageScanner
from kalshi_weather_arb.trader import Trader
from kalshi_weather_arb.backtest.engine import Backtester
from kalshi_weather_arb.backtest.data_loader import METARLoader, KalshiPriceLoader
from kalshi_weather_arb.backtest.report import BacktestReport


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Kalshi Weather Arbitrage CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # run command
    run_parser = subparsers.add_parser("run", help="Run the arbitrage loop")
    run_parser.add_argument(
        "--dashboard", action="store_true", help="Enable live dashboard view"
    )
    run_parser.add_argument(
        "--dry-run", action="store_true", help="Run in dry-run mode"
    )
    run_parser.add_argument("--api-key", required=True, help="Kalshi API key")
    run_parser.add_argument("--secret-key", required=True, help="Kalshi secret key")

    # scanner command
    scanner_parser = subparsers.add_parser(
        "scanner", help="Scan for arbitrage opportunities"
    )
    scanner_parser.add_argument("--ticker", default="KC", help="Kalshi ticker to scan")
    scanner_parser.add_argument(
        "--min-edge", type=float, default=0.05, help="Minimum edge threshold"
    )
    scanner_parser.add_argument(
        "--api-key", help="Kalshi API key (optional, for live data)"
    )
    scanner_parser.add_argument(
        "--secret-key", help="Kalshi secret key (optional, for live data)"
    )

    # backtest command
    backtest_parser = subparsers.add_parser("backtest", help="Run historical backtest")
    backtest_parser.add_argument(
        "--start", required=True, help="Start date (YYYY-MM-DD)"
    )
    backtest_parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    backtest_parser.add_argument("--station", default="KJFK", help="METAR station ID")
    backtest_parser.add_argument("--ticker", default="KC", help="Kalshi ticker")

    return parser.parse_args()


def run_loop(dashboard: bool, dry_run: bool, api_key: str, secret_key: str) -> None:
    """Run the arbitrage loop."""
    client = KalshiClient(api_key=api_key, secret_key=secret_key)
    scanner = ArbitrageScanner(client)
    trader = Trader(client)

    if dashboard:
        dash = Dashboard(dry_run=dry_run)
        dash.start()

    try:
        while True:
            # Simulate scan
            results = scanner.scan_contracts()
            if dashboard:
                dash.update(scan_results=results, ledger=trader.ledger)

            # Simulate trader
            if results:
                # Place a bet on first result
                trader.place_bet(
                    results[0].get("id", "unknown"), 100.0, dry_run=dry_run
                )
                if dashboard:
                    dash.update(ledger=trader.ledger)

    except KeyboardInterrupt:
        pass
    finally:
        if dashboard:
            dash.stop()


def run_scanner(
    ticker: str, min_edge: float, api_key: str = None, secret_key: str = None
) -> None:
    """Run the scanner and print opportunities."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    if api_key and secret_key:
        client = KalshiClient(api_key=api_key, secret_key=secret_key)
        scanner = ArbitrageScanner(client, min_edge=min_edge)
    else:
        from unittest.mock import MagicMock

        client = MagicMock(spec=KalshiClient)
        scanner = ArbitrageScanner(client, min_edge=min_edge)

    console.print(
        f"[bold blue]Scanning {ticker} markets for arbitrage opportunities...[/bold blue]"
    )
    console.print()

    opportunities = list(scanner.scan_opportunities())

    if not opportunities:
        console.print("[yellow]No opportunities found.[/yellow]")
        return

    table = Table(title=f"Arbitrage Opportunities ({len(opportunities)} found)")
    table.add_column("Ticker", style="cyan")
    table.add_column("Station", style="white")
    table.add_column("Threshold", style="white")
    table.add_column("Current Temp", style="white")
    table.add_column("Model Prob", style="green")
    table.add_column("Market Prob", style="blue")
    table.add_column("Edge", style="magenta")
    table.add_column("Ask (¢)", style="yellow")

    for opp in opportunities:
        table.add_row(
            opp.market_ticker,
            opp.station,
            f"{opp.threshold_f}°F",
            f"{opp.current_temp_f:.1f}°F",
            f"{opp.model_probability:.1%}",
            f"{opp.market_probability:.1%}",
            f"{opp.edge:.1%}",
            str(opp.ask_price_cents),
        )

    console.print(table)


def main() -> None:
    """CLI entry point."""
    args = parse_args()

    if args.command == "run":
        run_loop(
            dashboard=args.dashboard,
            dry_run=args.dry_run,
            api_key=args.api_key,
            secret_key=args.secret_key,
        )
    elif args.command == "backtest":
        print(
            f"Running backtest: {args.station} {args.ticker} "
            f"{args.start} to {args.end}"
        )
        metar_loader = METARLoader()
        price_loader = KalshiPriceLoader(api_key="dummy")
        backtester = Backtester(metar_loader, price_loader)
        results = backtester.run_backtest(
            station=args.station,
            ticker=args.ticker,
            start_date=args.start,
            end_date=args.end,
        )
        report = BacktestReport()
        report.print_summary(results)
    elif args.command == "scanner":
        run_scanner(
            ticker=args.ticker,
            min_edge=args.min_edge,
            api_key=getattr(args, "api_key", None),
            secret_key=getattr(args, "secret_key", None),
        )
    else:
        print("Usage: python -m kalshi_weather_arb <command>")
        print("Commands: run, scanner, backtest")
