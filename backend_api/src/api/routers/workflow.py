from datetime import datetime, timezone
from typing import Dict
from uuid import uuid4

from fastapi import APIRouter, Depends, Request

from src.api.core.security import get_current_user_token_data
from src.api.models.domain import TaskCreateRequest, TaskResponse
from src.api.services.audit_service import write_audit_log

router = APIRouter(prefix="/workflow", tags=["workflow"])

_TASKS: Dict[str, TaskResponse] = {}


@router.post(
    "/tasks",
    response_model=TaskResponse,
    summary="Create task",
    description="Create a workflow task (stub).",
    operation_id="workflow_tasks_create",
)
def create_task(req: TaskCreateRequest, token_data=Depends(get_current_user_token_data), request: Request = None):
    """Create a task (stub)."""
    task_id = str(uuid4())
    task = TaskResponse(id=task_id, title=req.title, status="open", created_at=datetime.now(timezone.utc))
    _TASKS[task_id] = task

    write_audit_log(
        actor_user_id=token_data.user_id,
        action="workflow.task.create",
        entity_type="task",
        entity_id=task_id,
        metadata={"application_id": req.application_id, "assignee_user_id": req.assignee_user_id},
        request=request,
    )
    return task


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Get task",
    description="Fetch a workflow task (stub).",
    operation_id="workflow_tasks_get",
)
def get_task(task_id: str, token_data=Depends(get_current_user_token_data)):
    """Get task (stub)."""
    return _TASKS[task_id]
