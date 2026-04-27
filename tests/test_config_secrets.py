"""Tests for config security — no hardcoded secrets."""

import os


def test_api_key_from_env():
    """CLI should read KALSHI_API_KEY from environment."""
    # Verify the cli.py source reads from env
    content = open("kalshi_weather_arb/cli.py").read()
    assert 'os.environ.get("KALSHI_API_KEY"' in content, \
        "cli.py should read KALSHI_API_KEY from environment"


def test_no_hardcoded_secrets_in_source():
    """Source files should not contain hardcoded secrets."""
    import subprocess
    result = subprocess.run(
        ["grep", "-rn", "--include=*.py",
         "-E", r"(secret[_-]?key|api[_-]?key|password|token)\s*=\s*['\"][^'\"{}$][^'\"{}$]*['\"]",
         "--exclude-dir=.venv", "--exclude-dir=__pycache__", "--exclude-dir=tests", "."],
        capture_output=True, text=True
    )
    # Filter out acceptable patterns
    lines = [
        l for l in result.stdout.split("\n") if l
        and "os.environ" not in l and "getenv" not in l
        and "dummy" not in l and "None" not in l
    ]
    assert not lines, f"Hardcoded secrets found: {lines}"


def test_env_example_exists():
    """.env.example should exist and document required secrets."""
    assert os.path.exists(".env.example"), ".env.example should exist"
    content = open(".env.example").read()
    assert "KALSHI_API_KEY" in content, ".env.example should document KALSHI_API_KEY"
    assert "KALSHI_SECRET_KEY" in content, ".env.example should document KALSHI_SECRET_KEY"


def test_gitignore_includes_env():
    """.gitignore should include .env."""
    content = open(".gitignore").read()
    assert ".env" in content, ".gitignore should include .env"
