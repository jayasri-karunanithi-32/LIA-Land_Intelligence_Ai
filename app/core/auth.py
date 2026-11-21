
import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError, PyJWKClientError

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger("lia")

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
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

jwks_client = PyJWKClient(
    JWKS_URL,
    headers={"User-Agent": "LIA-Backend/1.0"},
    timeout=10,
)

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    access_token: Optional[str] = Query(None),
):
    logger.info(
        "AUTH DEBUG: credentials=%s, token_present=%s",
        credentials is not None,
        bool(credentials and credentials.credentials)
    )

    token = None
    if credentials is not None:
        token = credentials.credentials
    elif access_token is not None:
        token = access_token

    logger.info("AUTH DEBUG: token extracted=%s", bool(token))

    # Keep the remaining existing code unchanged

    if not token or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = token.strip()

    try:
        # Determine signature algorithm from unverified header
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg", "ES256")

        valid_issuers = [JWT_ISSUER, f"{SUPABASE_URL}", "supabase"]

        if alg == "HS256" and SUPABASE_JWT_SECRET:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=valid_issuers,
                options={"require": ["exp", "sub"]},
                leeway=30,
            )
        else:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                audience="authenticated",
                issuer=valid_issuers,
                options={"require": ["exp", "sub"]},
                leeway=30,
            )

        return {
            "user_id": payload["sub"],
            "email": payload.get("email"),
            "role": payload.get("role"),
        }

    except Exception as exc:
        logger.error(
            "JWT verification failed [%s]: %s",
            type(exc).__name__,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
