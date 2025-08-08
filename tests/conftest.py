"""Pytest configuration for loading .env file."""

from pathlib import Path

from dotenv import load_dotenv


def pytest_configure():
    """Load .env file before running tests."""
    # Load .env file from the project root
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment variables from {env_file}")
    else:
        print(f"No .env file found at {env_file}")
