"""Test environment variable loading"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=== Environment Variables ===")
print(f"CORS_ORIGINS: {repr(os.getenv('CORS_ORIGINS'))}")
print(f"ALLOWED_EXTENSIONS: {repr(os.getenv('ALLOWED_EXTENSIONS'))}")
print(f"SECRET_KEY: {repr(os.getenv('SECRET_KEY'))}")
print(f"DATABASE_URL: {repr(os.getenv('DATABASE_URL'))}")
