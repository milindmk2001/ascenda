import os
from pathlib import Path
from dotenv import load_dotenv

# Show where Python is looking for .env
print(f"Looking in: {Path('.env').resolve()}")
print(f".env exists: {Path('.env').exists()}")

load_dotenv()

url = os.environ.get('DATABASE_DIRECT_URL', 'NOT FOUND')
print(f"DATABASE_DIRECT_URL: {url}")