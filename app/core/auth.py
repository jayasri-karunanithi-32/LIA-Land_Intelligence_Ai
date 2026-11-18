
import os

from pathlib import Path
from dotenv import load_dotenv

import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError, PyJWKClientError

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")

if not SUPABASE_URL:
    raise RuntimeError(
        "SUPABASE_URL is not configured. Please set SUPABASE_URL (or NEXT_PUBLIC_SUPABASE_URL) in your .env file."
    )

SUPABASE_URL = SUPABASE_URL.rstrip("/")

JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
JWT_ISSUER = f"{SUPABASE_URL}/auth/v1"

jwks_client = PyJWKClient(JWKS_URL)

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            issuer=JWT_ISSUER,
            options={
                "require": ["exp", "iat", "sub", "iss", "aud"]
            },
            leeway=30,
        )

        return {
            "user_id": payload["sub"],
            "email": payload.get("email"),
            "role": payload.get("role"),
        }

    except (PyJWTError, PyJWKClientError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
