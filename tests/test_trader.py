"""Tests for trader — dry-run ledger write, live mode mock."""

from unittest.mock import Mock, patch


from kalshi_weather_arb.trader import Trader  # noqa: F401


class TestTrader:
    """Test trader with mocked ledger and live mode."""

    def test_trader_initialization(self):
        """Test trader initialization."""
        mock_client = Mock()
        trader = Trader(mock_client, ledger_path="/tmp/ledger.json")
        assert trader.client == mock_client
        assert trader.ledger_path == "/tmp/ledger.json"
        assert trader.ledger == []

    def test_load_empty_ledger(self, tmp_path):
        """Test loading empty ledger."""
        ledger_file = tmp_path / "ledger.json"
        mock_client = Mock()
        trader = Trader(mock_client, ledger_path=str(ledger_file))
        trader.load_ledger()
        assert trader.ledger == []

    @patch("kalshi_weather_arb.client.KalshiClient.post")
    def test_dry_run_ledger(self, mock_post):
        """Test dry-run mode does not call post."""
        mock_client = Mock()
        mock_client.post = mock_post

        trader = Trader(mock_client, ledger_path="/tmp/ledger.json")

        # Dry-run mode: no real write
        result = trader.place_bet("contract-123", 100.0, dry_run=True)

        assert result["status"] == "dry_run"
        assert result["contract_id"] == "contract-123"
        assert result["amount"] == 100.0
        mock_post.assert_not_called()

    @patch("kalshi_weather_arb.client.KalshiClient.post")
    def test_live_mode(self, mock_post):
        """Test live mode calls post."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = {"id": "bet-456", "status": "placed"}

        mock_client = Mock()
        mock_client.post = mock_post

        trader = Trader(mock_client, ledger_path="/tmp/ledger.json")

        live_mode = False  # live_mode=False triggers post
        result = trader.place_bet("contract-123", 100.0, dry_run=live_mode)

        mock_post.assert_called_once()
        assert result["id"] == "bet-456"

    def test_ledger_entry(self):
        """Test ledger entry creation."""
        mock_client = Mock()
        trader = Trader(mock_client, ledger_path="/tmp/ledger.json")

        entry = trader.ledger_entry("contract-123", 100.0, True, 1.5)

        assert entry["contract_id"] == "contract-123"
        assert entry["amount"] == 100.0
        assert entry["win"] is True
        assert entry["odds"] == 1.5
        assert entry["profit"] == 50.0  # 100 * (1.5 - 1)
