
# SecureAI Passport

A security-focused AI action gateway built with Python and FastAPI.

## Overview

SecureAI Passport acts as a security layer between natural-language AI requests and application actions.

Instead of allowing AI to execute actions directly, it identifies the requested action and sends it through a controlled gateway.

## Features

- AI-powered natural-language request interpretation using Groq.
- API-key authentication.
- Predefined action allowlisting.
- Human approval workflow for sensitive actions.
- Audit logging.
- Audit event filtering.
- Input validation using Pydantic.
- Automated testing using Pytest.
- Prompt-injection-resistant system instructions.

## Technology Stack

- Python
- FastAPI
- Groq API
- OpenAI Python SDK
- Pydantic
- Pytest

## Project Structure

```text
SecureAI-Passport/
│
├── backend/
│   └── app/
│       ├── main.py
│       ├── ai.py
│       ├── auth.py
│       ├── approvals.py
│       ├── audit.py
│       ├── gateway.py
│       ├── policies.py
│       ├── schemas.py
│       └── tools.py
│
├── tests/
│   ├── test_ai_endpoint.py
│   ├── test_auth.py
│   ├── test_approvals.py
│   ├── test_gateway.py
│   └── test_policies.py
│
├── .env.example
├── .gitignore
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd SecureAI-Passport
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install fastapi uvicorn openai pytest httpx
```

### 5. Configure environment variables

Create a `.env` file or set these variables in your terminal:

```powershell
$env:SECUREAI_API_KEY="your_api_key"
$env:SECUREAI_APPROVER_ID="your_approver_id"
$env:GROQ_API_KEY="your_groq_api_key"
```

Never publish real API keys.

## Run the Application

```bash
python -m uvicorn app.main:app --app-dir backend --reload
```

Open the API documentation:

http://127.0.0.1:8000/docs

## Run Tests

```bash
python -m pytest -q
```

## Main API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /health | Health check |
| POST | /actions/execute | Execute an allowed action |
| POST | /ai/execute | Interpret and process AI requests |
| GET | /approvals | View approval requests |
| POST | /approvals/{id}/approve | Approve a request |
| POST | /approvals/{id}/reject | Reject a request |
| GET | /approvals/{id} | Check approval status |
| GET | /audit | View audit events |

## Security Design

The AI does not directly execute application actions.

Instead:

1. The user submits a natural-language request.
2. The AI identifies a predefined action.
3. The backend validates the returned action.
4. The gateway checks permissions and approval requirements.
5. The system records the outcome in the audit log.

## Current Limitations

- Customer-record deletion is simulated and is not actually implemented.
- Approval identity uses a demo identifier, not production-grade identity verification.
- JSON files are used for local persistence.
- Prompt-injection resistance is not guaranteed by system prompts alone.
- The project is an educational prototype, not a production-ready security system.

## License

MIT License
