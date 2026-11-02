from app.ai import understand_request
from fastapi import FastAPI, Depends, Header, HTTPException

from app.approvals import (
    list_approval_requests,
    get_approval_request,
    approve_request,
    reject_request,
)
from app.auth import require_api_key, require_approver
from app.audit import read_audit_events
from app.gateway import execute_action
from app.schemas import ActionRequest,AIRequest

app = FastAPI(title="SecureAI Passport")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/actions/execute")
def run_action(
    request: ActionRequest,
    authenticated: bool = Depends(require_api_key),
 ):
    return execute_action(request.action)



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



@app.get("/approvals")
def get_approval_requests(
    authenticated: bool = Depends(require_api_key),
):
    return {"approvals": list_approval_requests()}


@app.post("/approvals/{approval_id}/approve")
def approve_approval(
    approval_id: str,
    authenticated: bool = Depends(require_api_key),
    approver_id: str = Header(default="", alias="X-Approver-ID"),
):
    approver = require_approver(authenticated, approver_id)

    request = approve_request(approval_id, approver)

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found or already decided",
        )

    return {"approval": request}


@app.post("/approvals/{approval_id}/reject")
def reject_approval(
    approval_id: str,
    authenticated: bool = Depends(require_api_key),
    approver_id: str = Header(default="", alias="X-Approver-ID"),
):
    approver = require_approver(authenticated, approver_id)

    request = reject_request(approval_id, approver)

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found or already decided",
        )

    return {"approval": request}


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



@app.post("/ai/execute")
def ai_execute(
    request: AIRequest,
    authenticated: bool = Depends(require_api_key),
):
    try:
        action = understand_request(request.user_message)

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
