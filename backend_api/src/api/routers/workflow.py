from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.core.db import db_conn_cursor, get_database_config
from src.api.core.security import get_current_user_token_data
from src.api.models.domain import TaskCreateRequest, TaskResponse
from src.api.services.audit_service import write_audit_log

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post(
    "/tasks",
    response_model=TaskResponse,
    summary="Create task",
    description="Create a workflow task (Postgres-backed).",
    operation_id="workflow_tasks_create",
)
def create_task(req: TaskCreateRequest, token_data=Depends(get_current_user_token_data), request: Request = None):
    """Create a task (Postgres-backed)."""
    cfg = get_database_config()
    with db_conn_cursor(cfg.dsn) as (_, cur):
        cur.execute(
            """
            INSERT INTO workflow_tasks (
              title, description, status, application_id, assignee_user_id, created_by_user_id
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, title, status, created_at
            """,
            (
                req.title,
                req.description,
                "open",
                req.application_id,
                req.assignee_user_id,
                token_data.user_id,
            ),
        )
        row = cur.fetchone()

    task_id = str(row["id"])
    write_audit_log(
        actor_user_id=token_data.user_id,
        action="workflow.task.create",
        entity_type="task",
        entity_id=task_id,
        metadata={"application_id": req.application_id, "assignee_user_id": req.assignee_user_id},
        request=request,
    )
    return TaskResponse(id=task_id, title=row["title"], status=row["status"], created_at=row["created_at"])


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Get task",
    description="Fetch a workflow task from Postgres.",
    operation_id="workflow_tasks_get",
)
def get_task(task_id: str, token_data=Depends(get_current_user_token_data)):
    """Get task (Postgres-backed)."""
    cfg = get_database_config()
    with db_conn_cursor(cfg.dsn) as (_, cur):
        cur.execute(
            "SELECT id, title, status, created_at FROM workflow_tasks WHERE id=%s",
            (task_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(id=str(row["id"]), title=row["title"], status=row["status"], created_at=row["created_at"])
