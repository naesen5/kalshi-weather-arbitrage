"""Trader — place bets on Kalshi contracts."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from kalshi_weather_arb.client import KalshiClient


class Trader:
    """Trader — place bets on Kalshi contracts."""

    def __init__(self, client: KalshiClient, ledger_path: str = "ledger.json"):
        self.client = client
        self.ledger_path = ledger_path
        self.ledger: List[Dict[str, Any]] = []

    def load_ledger(self) -> None:
        """Load ledger from file."""
        try:
            with open(self.ledger_path, "r") as f:
                self.ledger = json.load(f)
        except FileNotFoundError:
            self.ledger = []

    def save_ledger(self) -> None:
        """Save ledger to file."""
        with open(self.ledger_path, "w") as f:
            json.dump(self.ledger, f, indent=2)

    def place_bet(
        self,
        contract_id: str,
        amount: float,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Place a bet on a contract."""
        if dry_run:
            return {"status": "dry_run", "contract_id": contract_id, "amount": amount}

        payload = {
            "contract_id": contract_id,
            "amount": amount,
            "timestamp": datetime.utcnow().isoformat(),
        }

        response = self.client.post("/api/v1/bets", payload)
        response["dry_run"] = False
        return response

    def ledger_entry(
        self,
        contract_id: str,
        amount: float,
        win: bool,
        odds: float,
    ) -> Dict[str, Any]:
        """Create a ledger entry."""
        return {
            "contract_id": contract_id,
            "amount": amount,
            "win": win,
            "odds": odds,
            "profit": amount * (odds - 1) if win else -amount,
            "timestamp": datetime.utcnow().isoformat(),
        }
