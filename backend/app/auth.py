
import logging
import os
import secrets

from fastapi import Depends, Header, HTTPException


logger = logging.getLogger(__name__)


def safe_equal(first: str, second: str) -> bool:
    """Compare secret values safely, including non-ASCII characters."""

    return secrets.compare_digest(
        first.encode("utf-8"),
        second.encode("utf-8"),
    )


def require_api_key(
    x_api_key: str = Header(default="", alias="X-API-Key"),
):
    expected_key = os.getenv("SECUREAI_API_KEY", "")

    if not expected_key:
        logger.error("SECUREAI_API_KEY is not configured")

        raise HTTPException(
            status_code=500,
            detail="Server authentication is not configured",
        )

    if not safe_equal(x_api_key, expected_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
        )

    return True


def require_approver(
    authenticated: bool = Depends(require_api_key),
    approver_token: str = Header(
        default="",
        alias="X-Approver-Token",
    ),
):
    expected_token = os.getenv(
        "SECUREAI_APPROVER_TOKEN",
        "",
    )

    approver_id = os.getenv(
        "SECUREAI_APPROVER_ID",
        "",
    )

    if not authenticated:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    if not expected_token or not approver_id:
        logger.error(
            "Approver authentication is not configured"
        )

        raise HTTPException(
            status_code=500,
            detail="Approver authentication is not configured",
        )

    if not safe_equal(approver_token, expected_token):
        raise HTTPException(
            status_code=403,
            detail="Invalid approver token",
        )

    return approver_id
