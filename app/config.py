import os
from dotenv import load_dotenv

load_dotenv()

secret_key = os.getenv("SECRET_KEY")

if not secret_key:
    raise ValueError("SECRET_KEY is not set")