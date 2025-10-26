"""
Configuration utility for loading Firefly III settings from environment variables.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def get_firefly_url() -> str:
    """
    Get Firefly III URL from environment variable.

    Returns:
        Firefly III URL (defaults to http://localhost if not set)
    """
    return os.getenv('FIREFLY_III_URL', 'http://localhost')


def get_firefly_token() -> str:
    """
    Get Firefly III API token from environment variable.

    Returns:
        Firefly III API token (defaults to empty string if not set)
    """
    return os.getenv('FIREFLY_III_TOKEN', '')


def is_configured() -> bool:
    """
    Check if Firefly III credentials are configured in .env file.

    Returns:
        True if both URL and token are set, False otherwise
    """
    url = get_firefly_url()
    token = get_firefly_token()
    return bool(url and url != 'http://localhost' or token)
