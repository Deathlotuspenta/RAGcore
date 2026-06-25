"""Background task status API."""

from fastapi import APIRouter, Depends

from server.auth.deps import get_current_user_id
from server.schemas import TaskItem, TaskAcceptedResponse
from server.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskItem])
def list_tasks(user_id: str = Depends(get_current_user_id)):
    return task_service.list_tasks(user_id)


@router.get("/{task_id}", response_model=TaskItem)
def get_task(task_id: str, user_id: str = Depends(get_current_user_id)):
    return task_service.get_task(user_id, task_id)
