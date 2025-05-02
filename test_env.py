import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
print(f"Loading .env from {BASE_DIR / '.env'}")
load_dotenv(BASE_DIR / '.env')

print("Environment variables:")
print(f"DB_HOST: {os.environ.get('DB_HOST')}")
print(f"DB_USER: {os.environ.get('DB_USER')}")
print(f"DB_NAME: {os.environ.get('DB_NAME')}")