# gidinest_backend/secrets_loader.py
"""
Load application secrets from AWS Secrets Manager (production)
or from .env file (local development).

Usage in settings.py:
    from gidinest_backend.secrets_loader import secrets
    SECRET_KEY = secrets["SECRET_KEY"]

Production: set ENVIRONMENT=production as an env var (e.g. in App Runner config).
Local dev:  .env file in the repo root is loaded automatically.
"""
import json
import os


def _load_from_aws():
    """Fetch secrets from AWS Secrets Manager and return as dict."""
    import boto3
    from botocore.exceptions import ClientError

    secret_name = os.getenv("AWS_SECRET_NAME", "gidinest/prod")
    region = os.getenv("AWS_REGION", "af-south-1")

    client = boto3.client("secretsmanager", region_name=region)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response["SecretString"])
    except ClientError as e:
        raise RuntimeError(f"Failed to load secrets from AWS Secrets Manager: {e}")


def _load_from_env():
    """Load secrets from .env file using python-dotenv."""
    from dotenv import dotenv_values
    from pathlib import Path

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return {}

    return dotenv_values(str(env_path))


class _EnvOverrideDict(dict):
    """
    Dict that checks os.environ first, then falls back to stored values.
    Returns empty string for missing keys instead of raising KeyError,
    so settings.py doesn't crash on optional keys.
    """

    def __getitem__(self, key):
        env_val = os.environ.get(key)
        if env_val is not None:
            return env_val
        try:
            return super().__getitem__(key)
        except KeyError:
            return ""

    def get(self, key, default=None):
        env_val = os.environ.get(key)
        if env_val is not None:
            return env_val
        return super().get(key, default)


def load_secrets():
    """
    Load secrets from the best available source.
    - ENVIRONMENT=production → AWS Secrets Manager
    - Otherwise → .env file
    Environment variables always override both.
    """
    if os.getenv("ENVIRONMENT") == "production":
        base = _load_from_aws()
    else:
        base = _load_from_env()

    return _EnvOverrideDict(base)


secrets = load_secrets()
