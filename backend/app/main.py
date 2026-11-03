
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.ai import understand_request
from app.approvals import (
    list_approval_requests,
    get_approval_request,
    approve_request,
    reject_request,
)
from app.auth import require_api_key, require_approver
from app.audit import read_audit_events
from app.gateway import execute_action
from app.schemas import ActionRequest, AIRequest


app = FastAPI(title="SecureAI Passport")


# Frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Execute an action
@app.post("/actions/execute")
def run_action(
    request: ActionRequest,
    authenticated: bool = Depends(require_api_key),
):
    result = execute_action(
        request.action,
        request.approval_id,
    )

    return result


# View audit events
@app.get("/audit")
def get_audit_events(
    action: str | None = None,
    status: str | None = None,
    approver_id: str | None = None,
    authenticated: bool = Depends(require_api_key),
):
    events = read_audit_events(
        action=action,
        status=status,
        approver_id=approver_id,
    )

    return {
        "total": len(events),
        "events": events,
    }


# View all approval requests
@app.get("/approvals")
def get_approval_requests(
    authenticated: bool = Depends(require_api_key),
):
    return {
        "approvals": list_approval_requests()
    }


# Approve a request
@app.post("/approvals/{approval_id}/approve")
def approve_approval(
    approval_id: str,
    approver: str = Depends(require_approver),
):
    request = approve_request(
        approval_id,
        approver,
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found, expired or already decided",
        )

    return {"approval": request}


# Reject a request
@app.post("/approvals/{approval_id}/reject")
def reject_approval(
    approval_id: str,
    approver: str = Depends(require_approver),
):
    request = reject_request(
        approval_id,
        approver,
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found, expired or already decided",
        )

    return {"approval": request}


# Check approval status
@app.get("/approvals/{approval_id}")
def get_approval_status(
    approval_id: str,
    authenticated: bool = Depends(require_api_key),
):
    request = get_approval_request(approval_id)

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found",
        )

    return {"approval": request}


# Execute an AI-interpreted action
@app.post("/ai/execute")
def ai_execute(
    request: AIRequest,
    authenticated: bool = Depends(require_api_key),
):
    try:
        action = understand_request(
            request.user_message
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable",
        )

    return execute_action(action)
