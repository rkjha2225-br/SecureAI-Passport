
import os
import secrets

from fastapi import Header, HTTPException


def require_api_key(
    x_api_key: str = Header(default=""),
):
    expected_key = os.getenv("SECUREAI_API_KEY", "")

    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="API key is not configured on the server",
        )

    if not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
        )

    return True


def require_approver(
    authenticated: bool,
    approver_id: str = Header(default=""),
):
    expected_approver = os.getenv("SECUREAI_APPROVER_ID", "")

    if not authenticated:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    if not expected_approver:
        raise HTTPException(
            status_code=500,
            detail="Approver identity is not configured",
        )

    if not secrets.compare_digest(approver_id, expected_approver):
        raise HTTPException(
            status_code=403,
            detail="Approver identity is invalid",
        )

    return approver_id
