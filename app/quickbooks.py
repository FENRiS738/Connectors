import httpx
import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Request, HTTPException

quickbooks_routes = APIRouter(prefix='/quickbooks/auth')

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

class GoogleOAuth:
    auth_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url: str = "https://oauth2.googleapis.com/token"
    revoke_url: str = "https://oauth2.googleapis.com/revoke"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def generate_auth_url(self, scope: str = "openid email profile") -> str:
        """Generate the Google authorization URL."""
        return (
            f"{self.auth_url}?"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"response_type=code&"
            f"scope={scope}&"
            f"access_type=offline"
        )
    
    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange the authorization code for access and refresh tokens."""
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=data)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to get token")
            return response.json()

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh the access token using the refresh token."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=data)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to refresh token")
            return response.json()

    async def revoke_token(self, token: str) -> dict:
        """Revoke the token."""
        data = {"token": token}
        async with httpx.AsyncClient() as client:
            response = await client.post(self.revoke_url, data=data)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to revoke token")
            return {"status": "revoked"}


oauth_client = GoogleOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI)

@quickbooks_routes.get("/login")
async def login():
    """Redirect user to Google login."""
    return {"url": oauth_client.generate_auth_url()}

@quickbooks_routes.get("/callback")
async def auth_callback(request: Request):
    """Handle the OAuth2 callback and exchange code for token."""
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Code not provided")
    tokens = await oauth_client.exchange_code_for_token(code)
    return {"tokens": tokens}

@quickbooks_routes.get("/refresh-token")
async def refresh_token(refresh_token: str):
    """Refresh access token."""
    tokens = await oauth_client.refresh_token(refresh_token)
    return {"tokens": tokens}

@quickbooks_routes.post("/revoke-token")
async def revoke_token(token: str):
    """Revoke access or refresh token."""
    status = await oauth_client.revoke_token(token)
    return status
