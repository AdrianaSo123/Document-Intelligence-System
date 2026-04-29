from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RequestContext:
    workspace_id: str
    user_id: str
    role: str
    trace_id: str


ROLE_OWNER = "OWNER"
ROLE_ANALYST = "ANALYST"
ROLE_AUDITOR = "AUDITOR"


def role_allows_write(role: str) -> bool:
    return role in {ROLE_OWNER, ROLE_ANALYST}


def role_allows_admin(role: str) -> bool:
    return role == ROLE_OWNER

