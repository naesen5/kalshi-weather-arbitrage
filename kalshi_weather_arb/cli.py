"""CLI — command-line interface for kalshi-weather-arbitrage."""

import argparse

from kalshi_weather_arb.client import KalshiClient
from kalshi_weather_arb.dashboard.display import Dashboard
from kalshi_weather_arb.scanner import Scanner
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

    # backtest command
    backtest_parser = subparsers.add_parser(
        "backtest", help="Run historical backtest"
    )
    backtest_parser.add_argument(
        "--start", required=True, help="Start date (YYYY-MM-DD)"
    )
    backtest_parser.add_argument(
        "--end", required=True, help="End date (YYYY-MM-DD)"
    )
    backtest_parser.add_argument(
        "--station", default="KJFK", help="METAR station ID"
    )
    backtest_parser.add_argument(
        "--ticker", default="KC", help="Kalshi ticker"
    )

    return parser.parse_args()


def run_loop(dashboard: bool, dry_run: bool, api_key: str, secret_key: str) -> None:
    """Run the arbitrage loop."""
    client = KalshiClient(api_key=api_key, secret_key=secret_key)
    scanner = Scanner(client)
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
        print(f"Running backtest: {args.station} {args.ticker} {args.start} to {args.end}")
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
    else:
        print("Usage: python -m kalshi_weather_arb <command>")
        print("Commands: run")
