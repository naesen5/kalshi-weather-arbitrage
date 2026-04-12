"""Risk state — track daily exposure, circuit breaker, and persistence."""

import csv
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

# Delayed import to avoid circular dependency
# from kalshi_weather_arb.trader.ledger import TradeLedger


class RiskState:
    """Risk state — track daily exposure with persistence."""

    def __init__(
        self,
        daily_max: float = 500.0,
        circuit_breaker_threshold: float = 50.0,
        max_daily_loss_dollars: float = 100.0,
        state_path: str = "state/risk.json",
    ):
        self.daily_max = daily_max
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.max_daily_loss_dollars = max_daily_loss_dollars
        self.daily_exposure = 0.0
        self.daily_pnl = 0.0
        self.open_positions = 0
        self.halted = False
        self.last_update = None
        self.state_path = state_path
        self._load_state()

    def _load_state(self) -> None:
        """Load state from file if exists."""
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r") as f:
                    data = json.load(f)
                    self.daily_exposure = data.get("daily_exposure", 0.0)
                    self.daily_pnl = data.get("daily_pnl", 0.0)
                    self.open_positions = data.get("open_positions", 0)
                    self.halted = data.get("halted", False)
                    self.last_update = datetime.fromisoformat(data.get("last_update", ""))
                    self._check_circuit_breaker()
            except Exception:
                pass

    def _save_state(self) -> None:
        """Save state to file."""
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        data = {
            "daily_exposure": self.daily_exposure,
            "daily_pnl": self.daily_pnl,
            "open_positions": self.open_positions,
            "halted": self.halted,
            "last_update": datetime.utcnow().isoformat(),
        }
        with open(self.state_path, "w") as f:
            json.dump(data, f, indent=2)
        os.chmod(self.state_path, 0o600)

    def _check_circuit_breaker(self) -> None:
        """Check if circuit breaker should trigger."""
        if self.daily_pnl < -self.circuit_breaker_threshold:
            self.halted = True
            self._save_state()
            print(f"⚠️ Circuit breaker triggered: daily_pnl={self.daily_pnl:.2f} < -{self.circuit_breaker_threshold}")

    def update_from_ledger(self, ledger_path: str) -> None:
        """Update risk state from ledger file."""
        entries = self._read_ledger(ledger_path)
        today = datetime.utcnow().date()
        total_exposure = 0.0
        total_pnl = 0.0
        open_positions = 0

        for entry in entries:
            entry_date = datetime.fromisoformat(entry["timestamp"]).date()
            if entry_date == today:
                cost = float(entry.get("cost_dollars", 0))
                fill_price = float(entry.get("fill_price_cents", 0))
                if fill_price > 0:
                    total_exposure += fill_price / 100.0
                else:
                    total_exposure += cost

                # Track PnL (positive = won, negative = lost)
                status = entry.get("status", "")
                if status == "filled":
                    total_pnl += fill_price / 100.0 - cost
                elif status == "rejected":
                    total_pnl -= cost

                if entry.get("status") not in ["filled", "cancelled"]:
                    open_positions += 1

        self.daily_exposure = total_exposure
        self.daily_pnl = total_pnl
        self.open_positions = open_positions
        self.last_update = datetime.utcnow()
        self._check_circuit_breaker()
        self._save_state()

    def _read_ledger(self, ledger_path: str) -> List[Dict[str, Any]]:
        """Read ledger entries from file."""
        if not os.path.exists(ledger_path):
            return []
        entries = []
        with open(ledger_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append(row)
        return entries

    def can_afford(self, cost_dollars: float) -> bool:
        """Check if risk state can afford this cost."""
        if self.halted:
            return False
        return self.daily_exposure + cost_dollars <= self.daily_max

    def record_bet(self, cost_dollars: float, result: str) -> None:
        """Record a bet result and update state."""
        if result == "won":
            self.daily_pnl += cost_dollars
        elif result == "lost":
            self.daily_pnl -= cost_dollars
        self._save_state()
        self._check_circuit_breaker()

    def reset_daily(self) -> None:
        """Reset daily state at midnight."""
        self.daily_exposure = 0.0
        self.daily_pnl = 0.0
        self.open_positions = 0
        self.halted = False
        self._save_state()
