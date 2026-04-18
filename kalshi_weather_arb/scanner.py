"""Scanner — scan for weather contracts on Kalshi and identify arbitrage opportunities."""

from typing import Generator, Optional

from kalshi_weather_arb.client import KalshiClient
from kalshi_weather_arb.metar.client import METARClient
from kalshi_weather_arb.metar.mapper import StationMapper
from kalshi_weather_arb.probability_model import TemperatureProbModel
from kalshi_weather_arb.title_parser import parse_temperature_title, TitleParsed
from kalshi_weather_arb.models import Opportunity


class ArbitrageScanner:
    """
    Scan Kalshi temperature markets for arbitrage opportunities.

    For each open weather market:
    1. Fetch current METAR observation for the city
    2. Parse market title to extract threshold and direction
    3. Calculate probability that daily high > threshold
    4. Compare model probability to market implied probability
    5. Yield opportunities where edge exceeds threshold
    """

    def __init__(
        self,
        client: KalshiClient,
        metar_client: Optional[METARClient] = None,
        mapper: Optional[StationMapper] = None,
        model: Optional[TemperatureProbModel] = None,
        min_edge: float = 0.05,
        max_obs_age_minutes: float = 90.0,
    ):
        """
        Initialize the scanner.

        Args:
            client: Kalshi API client
            metar_client: METAR data client (creates default if None)
            mapper: Station mapper for ICAO→city matching (creates default if None)
            model: Temperature probability model (creates default if None)
            min_edge: Minimum edge (model_prob - market_prob) to consider tradeable
            max_obs_age_minutes: Maximum age of METAR observation to use
        """
        self.client = client
        self.metar_client = metar_client or METARClient()
        self.mapper = mapper or StationMapper()
        self.model = model or TemperatureProbModel()
        self.min_edge = min_edge
        self.max_obs_age_minutes = max_obs_age_minutes

    def _get_markets(self, tickers: list[str]) -> list[dict]:
        """
        Fetch markets from Kalshi API.

        Args:
            tickers: List of ticker symbols to fetch

        Returns:
            List of market dicts
        """
        try:
            # Use paginate to fetch all markets
            markets = self.client.paginate("/markets")
            # Filter to requested tickers (check if ticker starts with any prefix)
            if tickers:
                return [
                    m
                    for m in markets
                    if any(m.get("ticker", "").startswith(t) for t in tickers)
                ]
            return markets
        except Exception:
            return []

    def _get_metar(self, station: str) -> Optional[dict]:
        """
        Fetch METAR observation for a station.

        Args:
            station: ICAO station code (e.g., 'KJFK')

        Returns:
            METAR dict or None if not found
        """
        try:
            observations = self.metar_client.fetch([station])
            if observations:
                obs = observations[0]
                return {
                    "icao": obs.icao,
                    "temp": obs.temp_c,
                    "dewpoint": obs.dewpoint,
                    "obsTime": obs.obs_time.isoformat(),
                }
            return None
        except Exception:
            return None

    def _parse_title(self, title: str) -> Optional[TitleParsed]:
        """
        Parse market title to extract city and threshold.

        Args:
            title: Market title string

        Returns:
            TitleParsed or None if not a temperature market
        """
        return parse_temperature_title(title)

    def _get_station(self, city: str) -> Optional[str]:
        """
        Get ICAO station code for a city.

        Args:
            city: City name

        Returns:
            ICAO station code or None if not found
        """
        return self.mapper.get_station(city)

    def _get_obs_age_minutes(self, metar: dict) -> float:
        """
        Calculate age of METAR observation in minutes.

        Args:
            metar: METAR dict with obsTime

        Returns:
            Age in minutes
        """
        from datetime import datetime, timezone

        obs_time_str = metar.get("obsTime", "")
        if not obs_time_str:
            return 999.0

        try:
            obs_time = datetime.fromisoformat(obs_time_str.replace("Z", "+00:00"))
        except ValueError:
            return 999.0

        now = datetime.now(timezone.utc)
        age_seconds = (now - obs_time).total_seconds()
        return age_seconds / 60.0

    def _calculate_probability(
        self,
        metar: dict,
        threshold_f: float,
    ) -> tuple[float, float, float]:
        """
        Calculate probability that daily high exceeds threshold.

        Args:
            metar: METAR dict with temp, dewpoint, obsTime
            threshold_f: Temperature threshold in Fahrenheit

        Returns:
            Tuple of (probability, temp_f, dewpoint_f)
        """
        from datetime import datetime, timezone

        # Convert Celsius to Fahrenheit
        temp_c = metar.get("temp", 0.0)
        dewpoint_c = metar.get("dewpoint")

        temp_f = temp_c * 9.0 / 5.0 + 32.0
        dewpoint_f = dewpoint_c * 9.0 / 5.0 + 32.0 if dewpoint_c is not None else 32.0

        # Parse hour of day
        obs_time_str = metar.get("obsTime", "")
        if not obs_time_str:
            hour_of_day = 12.0
        else:
            try:
                obs_time = datetime.fromisoformat(obs_time_str.replace("Z", "+00:00"))
            except ValueError:
                obs_time = datetime.now(timezone.utc)

        hour_of_day = obs_time.hour + (obs_time.minute / 60.0)

        prob = self.model.p_exceed(
            current_temp_f=temp_f,
            dewpoint_f=dewpoint_f,
            hour_of_day=hour_of_day,
            threshold_f=threshold_f,
        )

        return prob, temp_f, dewpoint_f

    def scan_opportunities(self) -> Generator[Opportunity, None, None]:
        """
        Scan all open weather markets for arbitrage opportunities.

        Yields:
            Opportunity objects where model probability exceeds market probability
            by more than min_edge threshold.
        """
        markets = self._get_markets(tickers=["KC", "KT"])

        for market in markets:
            if market.get("category") != "weather":
                continue

            ticker = market.get("ticker", "")
            title = market.get("title", "")
            yes_ask = market.get("yesAsk", 100)

            parsed = self._parse_title(title)
            if not parsed:
                continue

            station = self._get_station(parsed.city)
            if not station:
                continue

            metar = self._get_metar(station)
            if not metar:
                continue

            obs_age = self._get_obs_age_minutes(metar)
            if obs_age > self.max_obs_age_minutes:
                continue

            model_prob, temp_f, dewpoint_f = self._calculate_probability(
                metar, parsed.threshold_f
            )
            market_prob = yes_ask / 100.0
            edge = model_prob - market_prob

            if edge >= self.min_edge:
                opportunity = Opportunity(
                    market_ticker=ticker,
                    market_title=title,
                    station=station,
                    current_temp_f=temp_f,
                    obs_age_minutes=obs_age,
                    threshold_f=parsed.threshold_f,
                    model_probability=model_prob,
                    market_probability=market_prob,
                    edge=edge,
                    ask_price_cents=int(yes_ask),
                    recommended_side="yes",
                )
                yield opportunity

    def scan_for_ticker(
        self,
        ticker: str,
        city: str,
    ) -> Optional[Opportunity]:
        """
        Scan a specific ticker for a single opportunity.

        Args:
            ticker: Kalshi ticker (e.g., 'KC-JFK-90')
            city: City name for METAR lookup

        Returns:
            Opportunity if found and tradeable, None otherwise
        """
        markets = self._get_markets(tickers=[ticker])
        if not markets:
            return None

        market = markets[0]
        title = market.get("title", "")
        yes_ask = market.get("yesAsk", 100)

        parsed = self._parse_title(title)
        if not parsed:
            return None

        station = self._get_station(city)
        if not station:
            return None

        metar = self._get_metar(station)
        if not metar:
            return None

        obs_age = self._get_obs_age_minutes(metar)
        if obs_age > self.max_obs_age_minutes:
            return None

        model_prob, temp_f, dewpoint_f = self._calculate_probability(
            metar, parsed.threshold_f
        )
        market_prob = yes_ask / 100.0
        edge = model_prob - market_prob

        if edge >= self.min_edge:
            return Opportunity(
                market_ticker=ticker,
                market_title=title,
                station=station,
                current_temp_f=temp_f,
                obs_age_minutes=obs_age,
                threshold_f=parsed.threshold_f,
                model_probability=model_prob,
                market_probability=market_prob,
                edge=edge,
                ask_price_cents=int(yes_ask),
                recommended_side="yes",
            )

        return None
