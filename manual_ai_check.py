
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent / "backend"),
)

from app.ai import understand_request


user_message = "Show me all demo records."

action = understand_request(user_message)

print("User request:", user_message)
print("AI selected action:", action)
