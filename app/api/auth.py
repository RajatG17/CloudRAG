import os
from dataclasses import dataclass

from fastapi import HTTPException, Request, status


@dataclass(frozen=True)
class AuthContext:
    subject: str
    tenant_id: str

def require_user(request: Request) -> AuthContext:

    event = request.scope.get("aws.event")

    if not isinstance(event, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated API Gateway request expired",
        )

    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )

    expected_client = os.environ.get(
        "COGNITO_APP_CLIENT_ID"
    )

    subject = claims.get("sub")

    if (
        not expected_client 
        or claims.get('token_use') != "access"
        or claims.get("client_id") != expected_client
        or not subject
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication context",
        )

    return AuthContext(
        subject=subject,
        tenant_id=os.getenv(
            "CLOUDRAG_DEFAULT_TENANT",
            "demo"
        ),
    )