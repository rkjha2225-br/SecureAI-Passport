
DEMO_RECORDS = [
    {"id": "REC-001", "name": "Demo ticket A"},
    {"id": "REC-002", "name": "Demo ticket B"},
    {"id": "REC-003", "name": "Demo ticket C"},
]


def read_demo_records():
    # Return copies so the original records cannot be modified accidentally.
    return [record.copy() for record in DEMO_RECORDS]
