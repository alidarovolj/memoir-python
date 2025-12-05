"""API v1 routes"""
from fastapi import APIRouter
from app.api.v1 import auth, sms_auth, memories, categories, search, smart_search, stories, tasks, task_ai, subtasks, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(sms_auth.router, prefix="/sms-auth", tags=["sms-auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(memories.router, prefix="/memories", tags=["memories"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(smart_search.router, prefix="/smart-search", tags=["smart-search"])
api_router.include_router(stories.router, prefix="/stories", tags=["stories"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(task_ai.router, prefix="/task-ai", tags=["task-ai"])
api_router.include_router(subtasks.router, prefix="/tasks/{task_id}/subtasks", tags=["subtasks"])

