"""API v1 routes"""
from fastapi import APIRouter
from app.api.v1 import auth, sms_auth, email_auth, memories, categories, search, smart_search, stories, tasks, task_groups, task_ai, subtasks, users, analytics, pets, pet_shop, pet_games, pet_social, pet_journal, time_capsules, daily_prompts, challenges, ai_stories, achievements, voice, friends, memory_sharing, memory_reactions, group_challenges

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(sms_auth.router, prefix="/sms-auth", tags=["sms-auth"])
api_router.include_router(email_auth.router, prefix="/email-auth", tags=["email-auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(memories.router, prefix="/memories", tags=["memories"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(smart_search.router, prefix="/smart-search", tags=["smart-search"])
api_router.include_router(stories.router, prefix="/stories", tags=["stories"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(task_groups.router, prefix="/task-groups", tags=["task-groups"])
api_router.include_router(task_ai.router, prefix="/task-ai", tags=["task-ai"])
api_router.include_router(subtasks.router, prefix="/tasks/{task_id}/subtasks", tags=["subtasks"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(pets.router, prefix="/pets", tags=["pets"])
api_router.include_router(pet_shop.router, prefix="/pets", tags=["pet-shop"])
api_router.include_router(pet_games.router, prefix="/pets", tags=["pet-games"])
api_router.include_router(pet_social.router, prefix="/pets", tags=["pet-social"])
api_router.include_router(pet_journal.router, prefix="/pets", tags=["pet-journal"])
api_router.include_router(time_capsules.router, prefix="/time-capsules", tags=["time-capsules"])
api_router.include_router(daily_prompts.router, prefix="/daily-prompts", tags=["daily-prompts"])
api_router.include_router(challenges.router, prefix="/challenges", tags=["challenges"])
api_router.include_router(ai_stories.router, prefix="/ai", tags=["ai-stories"])
api_router.include_router(achievements.router, prefix="/achievements", tags=["achievements"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
api_router.include_router(friends.router, prefix="/friends", tags=["friends"])
api_router.include_router(memory_sharing.router, prefix="/memories/sharing", tags=["memory-sharing"])
api_router.include_router(memory_reactions.router, prefix="/memories", tags=["memory-reactions"])
api_router.include_router(group_challenges.router, prefix="/social", tags=["group-challenges"])


