import json
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import Request

from src.api.core.db import db_conn_cursor, get_database_config
from src.api.core.logging import get_logger, log_kv

logger = get_logger(__name__)


# PUBLIC_INTERFACE
def write_audit_log(
    *,
    actor_user_id: Optional[str],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> str:
    """Write an audit log entry to Postgres.

    Contract:
      - This is the single canonical entrypoint for audit logging.
      - All routers should call this for security-relevant or workflow-relevant actions.
      - Metadata is stored as JSONB.

    Inputs:
      - actor_user_id: UUID string or None
      - action: stable action name, e.g. "auth.login", "applications.create"
      - entity_type/entity_id: optional linkage
      - metadata: optional dict
      - request: optional FastAPI Request (used for IP / UA capture)

    Outputs:
      - audit_log id (UUID string)

    Errors:
      - Postgres connection / execution errors.

    Side effects:
      - Inserts into audit_log table.
    """
    cfg = get_database_config()
    audit_id = uuid4()
    meta = metadata or {}

    ip_address = None
    user_agent = None
    if request is not None:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    log_kv(
        logger,
        "audit_log:write",
        audit_id=str(audit_id),
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    with db_conn_cursor(cfg.dsn) as (_, cur):
        cur.execute(
            """
            INSERT INTO audit_log (id, actor_user_id, action, entity_type, entity_id, metadata, ip_address, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
            """,
            (
                str(audit_id),
                actor_user_id,
                action,
                entity_type,
                entity_id,
                json.dumps(meta),
                ip_address,
                user_agent,
            ),
        )
    return str(audit_id)
