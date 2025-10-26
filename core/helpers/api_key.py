import secrets
import string

def generate_api_key(length=32):
    """Generate a random API key with the given length."""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))
