"""Trade ledger — append-only CSV for trade records."""

import csv
import os
from datetime import datetime
from typing import Any, Dict, List


class TradeLedger:
    """Trade ledger — append-only CSV for trade records."""

    def __init__(self, ledger_path: str):
        self.ledger_path = ledger_path

    def _ensure_file_exists(self) -> None:
        """Create ledger file with header if it doesn exist."""
        if not os.path.exists(self.ledger_path):
            with open(self.ledger_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "order_id",
                    "ticker",
                    "side",
                    "count",
                    "price_cents",
                    "cost_dollars",
                    "model_prob",
                    "market_prob",
                    "edge",
                    "dry_run",
                    "fill_price_cents",
                    "status",
                ])

    def append_row(self, **kwargs) -> None:
        """Append a row to the ledger."""
        self._ensure_file_exists()
        with open(self.ledger_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                kwargs.get("timestamp", datetime.utcnow().isoformat()),
                kwargs.get("order_id", ""),
                kwargs.get("ticker", ""),
                kwargs.get("side", ""),
                kwargs.get("count", 0),
                kwargs.get("price_cents", 0),
                kwargs.get("cost_dollars", 0.0),
                kwargs.get("model_prob", 0.0),
                kwargs.get("market_prob", 0.0),
                kwargs.get("edge", 0.0),
                kwargs.get("dry_run", False),
                kwargs.get("fill_price_cents", 0),
                kwargs.get("status", ""),
            ])

    def read_all(self) -> List[Dict[str, Any]]:
        """Read all entries from the ledger."""
        self._ensure_file_exists()
        entries = []
        with open(self.ledger_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append(row)
        return entries
