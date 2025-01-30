import os

SECRET_KEY_ENV = "SECRET_KEY_PATH"
SECRET_KEY_PATH = os.getenv(SECRET_KEY_ENV, '')

API_KEY_ENV = "API_KEY_PATH"
API_KEY_PATH = os.getenv("API_KEY_PATH", '')

def get_secret_key() -> str:
    with open(SECRET_KEY_PATH, 'r') as f:
        return f.read().strip()

def get_api_key() -> str:
    with open(API_KEY_PATH, 'r') as f:
        return f.read().strip()