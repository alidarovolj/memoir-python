"""User XP / rank service.

XP is awarded to the *user* (not just the pet) when they perform key actions.
Rank is computed on the fly from the XP total.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


# ---------------------------------------------------------------------------
# Rank definitions
# ---------------------------------------------------------------------------

class Rank(str, Enum):
    NEWBIE     = "newbie"
    STARTER    = "starter"
    EXPLORER   = "explorer"
    ADEPT      = "adept"
    MASTER     = "master"
    LEGEND     = "legend"


# (min_xp, rank, label_en, emoji)
RANK_TIERS: list[tuple[int, Rank, str, str]] = [
    (0,    Rank.NEWBIE,   "Newbie",   "🌱"),
    (50,   Rank.STARTER,  "Starter",  "⚡"),
    (150,  Rank.EXPLORER, "Explorer", "🔥"),
    (350,  Rank.ADEPT,    "Adept",    "💫"),
    (700,  Rank.MASTER,   "Master",   "💎"),
    (1500, Rank.LEGEND,   "Legend",   "👑"),
]

# XP per action
XP_TASK_LOW      = 5
XP_TASK_MEDIUM   = 10
XP_TASK_HIGH     = 15
XP_TASK_CRITICAL = 20
XP_MEMORY        = 5
XP_STORY         = 8
XP_CHALLENGE     = 50
XP_ACHIEVEMENT   = 15   # base bonus on top of achievement.xp_reward


def get_rank_info(xp: int) -> dict:
    """Return rank dict for the given XP total."""
    tier = RANK_TIERS[0]
    for t in RANK_TIERS:
        if xp >= t[0]:
            tier = t

    # Next tier
    tier_idx = RANK_TIERS.index(tier)
    if tier_idx + 1 < len(RANK_TIERS):
        next_tier = RANK_TIERS[tier_idx + 1]
        xp_for_next = next_tier[0]
        xp_in_tier  = xp - tier[0]
        xp_needed   = next_tier[0] - tier[0]
        progress    = xp_in_tier / xp_needed
    else:
        xp_for_next = None
        progress    = 1.0
        xp_needed   = 0

    return {
        "xp":          xp,
        "rank":        tier[1].value,
        "rank_label":  tier[2],
        "rank_emoji":  tier[3],
        "xp_for_next": xp_for_next,
        "progress":    round(progress, 4),
    }


async def award_xp(
    db: AsyncSession,
    user_id,
    amount: int,
    reason: Optional[str] = None,
) -> int:
    """Add *amount* XP to user and return new total."""
    from app.models.user import User
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or amount <= 0:
        return 0
    user.xp = (user.xp or 0) + amount
    return user.xp
