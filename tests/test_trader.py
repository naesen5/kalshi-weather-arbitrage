"""Tests for AutoTrader — dry-run ledger write, live mode mock."""

from unittest.mock import Mock, patch
from pathlib import Path
import tempfile

from kalshi_weather_arb.trader.auto_trader import AutoTrader, RiskState
from kalshi_weather_arb.trader.ledger import TradeLedger


class TestAutoTrader:
    """Test AutoTrader with mocked ledger and live mode."""

    def test_trader_initialization(self):
        """Test AutoTrader initialization."""
        mock_client = Mock()
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.csv"
            ledger = TradeLedger(str(ledger_path))
            risk_state = RiskState()
            trader = AutoTrader(mock_client, ledger, risk_state)
            assert trader.client == mock_client
            assert trader.ledger == ledger
            assert trader.risk_state == risk_state

    def test_load_empty_ledger(self):
        """Test loading empty ledger."""
        mock_client = Mock()
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.csv"
            ledger = TradeLedger(str(ledger_path))
            risk_state = RiskState()
            trader = AutoTrader(mock_client, ledger, risk_state)
            entries = ledger.read_all()
            assert entries == []

    def test_dry_run_ledger(self):
        """Test dry-run mode does not call post."""
        mock_client = Mock()
        mock_client.post = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.csv"
            ledger = TradeLedger(str(ledger_path))
            risk_state = RiskState()
            trader = AutoTrader(mock_client, ledger, risk_state, dry_run=True)

            spec = {
                "ticker": "CL",
                "side": "high",
                "count": 1,
                "price_cents": 110,
                "model_prob": 0.6,
                "market_prob": 0.5,
                "edge": 0.1,
            }
            result = trader.execute(spec)

            assert result.status == "dry_run"
            assert result.dry_run is True
            mock_client.post.assert_not_called()

    def test_live_mode(self):
        """Test live mode calls post."""
        mock_response = {"order_id": "order-456", "status": "placed"}

        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.csv"
            ledger = TradeLedger(str(ledger_path))
            risk_state = RiskState()
            # Set risk state to allow the test bet
            risk_state.daily_exposure = 100.0  # below 500 max
            risk_state.daily_max = 500.0
            
            # Create a real KalshiClient and patch its post method
            from kalshi_weather_arb.client import KalshiClient
            client = KalshiClient("https://demo.kalshi.com", "test-key")
            
            with patch.object(client, 'post', return_value=mock_response) as mock_post:
                trader = AutoTrader(client, ledger, risk_state, dry_run=False)

                spec = {
                    "ticker": "CL",
                    "side": "high",
                    "count": 1,
                    "price_cents": 110,  # $1.10
                    "model_prob": 0.6,
                    "market_prob": 0.5,
                    "edge": 0.1,
                }
                result = trader.execute(spec)

                # Live mode should call post
                mock_post.assert_called_once()
                assert result.status == "placed"
                assert result.dry_run is False

    def test_ledger_entry(self):
        """Test ledger entry creation."""
        mock_client = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = Path(tmpdir) / "ledger.csv"
            ledger = TradeLedger(str(ledger_path))
            risk_state = RiskState()
            trader = AutoTrader(mock_client, ledger, risk_state)

            spec = {
                "ticker": "CL",
                "side": "high",
                "count": 1,
                "price_cents": 110,
                "model_prob": 0.6,
                "market_prob": 0.5,
                "edge": 0.1,
            }
            result = trader.execute(spec)

            assert result.order_id.startswith("dry_run_")
            assert result.filled is True
            assert result.dry_run is True
            assert result.status == "dry_run"
