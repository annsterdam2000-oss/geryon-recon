# server/deps.py
from fastapi import Header, HTTPException
from config import API_TOKEN

async def verify_token(x_api_key: str = Header(None)):
    if x_api_key != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")
    return x_api_key