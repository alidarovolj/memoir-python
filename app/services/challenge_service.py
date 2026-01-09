"""Challenge service for community engagement features"""
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.models.challenge import GlobalChallenge, ChallengeParticipant
from app.models.user import User
from app.schemas.challenge import GlobalChallengeCreate, GlobalChallengeUpdate


class ChallengeService:
    """Service for managing challenges and participants"""
    
    @staticmethod
    async def create_challenge(
        db: AsyncSession,
        challenge_data: GlobalChallengeCreate,
    ) -> GlobalChallenge:
        """Create a new challenge"""
        challenge = GlobalChallenge(**challenge_data.dict())
        db.add(challenge)
        await db.commit()
        await db.refresh(challenge)
        return challenge
    
    @staticmethod
    async def get_active_challenges(
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[GlobalChallenge], int]:
        """Get all active challenges (ongoing or upcoming)"""
        now = datetime.now(timezone.utc)
        
        # Query for active challenges
        query = select(GlobalChallenge).where(
            and_(
                GlobalChallenge.is_active == True,
                GlobalChallenge.end_date >= now,  # Not ended yet
            )
        ).order_by(GlobalChallenge.start_date.asc())
        
        # Count total
        count_query = select(func.count()).select_from(GlobalChallenge).where(
            and_(
                GlobalChallenge.is_active == True,
                GlobalChallenge.end_date >= now,
            )
        )
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Paginate
        skip = (page - 1) * size
        query = query.offset(skip).limit(size)
        
        result = await db.execute(query)
        challenges = result.scalars().all()
        
        return list(challenges), total
    
    @staticmethod
    async def get_challenge_by_id(
        db: AsyncSession,
        challenge_id: str,
    ) -> Optional[GlobalChallenge]:
        """Get challenge by ID"""
        query = select(GlobalChallenge).where(GlobalChallenge.id == UUID(challenge_id))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def join_challenge(
        db: AsyncSession,
        challenge_id: str,
        user_id: str,
    ) -> ChallengeParticipant:
        """Join a challenge"""
        # Check if already participating
        existing_query = select(ChallengeParticipant).where(
            and_(
                ChallengeParticipant.challenge_id == UUID(challenge_id),
                ChallengeParticipant.user_id == UUID(user_id),
            )
        )
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            return existing
        
        # Create participation
        participant = ChallengeParticipant(
            challenge_id=UUID(challenge_id),
            user_id=UUID(user_id),
            progress=0,
            completed=False,
        )
        db.add(participant)
        
        # Increment participants count
        challenge_query = select(GlobalChallenge).where(GlobalChallenge.id == UUID(challenge_id))
        challenge_result = await db.execute(challenge_query)
        challenge = challenge_result.scalar_one()
        challenge.participants_count += 1
        
        await db.commit()
        await db.refresh(participant)
        
        return participant
    
    @staticmethod
    async def get_user_progress(
        db: AsyncSession,
        challenge_id: str,
        user_id: str,
    ) -> Optional[ChallengeParticipant]:
        """Get user's progress in a specific challenge"""
        query = select(ChallengeParticipant).where(
            and_(
                ChallengeParticipant.challenge_id == UUID(challenge_id),
                ChallengeParticipant.user_id == UUID(user_id),
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_progress(
        db: AsyncSession,
        challenge_id: str,
        user_id: str,
        increment: int = 1,
    ) -> ChallengeParticipant:
        """Update user's progress in a challenge"""
        participant = await ChallengeService.get_user_progress(db, challenge_id, user_id)
        
        if not participant:
            raise ValueError("User is not participating in this challenge")
        
        # Update progress
        participant.progress += increment
        
        # Check if goal is reached
        challenge = await ChallengeService.get_challenge_by_id(db, challenge_id)
        target = challenge.goal.get("target", 0)
        
        if participant.progress >= target and not participant.completed:
            participant.completed = True
            participant.completed_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(participant)
        
        return participant
    
    @staticmethod
    async def get_leaderboard(
        db: AsyncSession,
        challenge_id: str,
        limit: int = 100,
    ) -> List[dict]:
        """Get challenge leaderboard with user rankings"""
        query = (
            select(
                ChallengeParticipant,
                User.username,
                User.avatar_url,
            )
            .join(User, ChallengeParticipant.user_id == User.id)
            .where(ChallengeParticipant.challenge_id == UUID(challenge_id))
            .order_by(
                ChallengeParticipant.completed.desc(),
                ChallengeParticipant.progress.desc(),
                ChallengeParticipant.joined_at.asc(),
            )
            .limit(limit)
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        # Get challenge for target
        challenge = await ChallengeService.get_challenge_by_id(db, challenge_id)
        target = challenge.goal.get("target", 1)
        
        # Build leaderboard
        leaderboard = []
        for rank, (participant, username, avatar_url) in enumerate(rows, start=1):
            percentage = min((participant.progress / target) * 100, 100) if target > 0 else 0
            leaderboard.append({
                "rank": rank,
                "user_id": str(participant.user_id),
                "username": username,
                "avatar_url": avatar_url,
                "progress": participant.progress,
                "completed": participant.completed,
                "percentage": round(percentage, 1),
            })
        
        return leaderboard
    
    @staticmethod
    async def get_user_challenges(
        db: AsyncSession,
        user_id: str,
    ) -> List[dict]:
        """Get all challenges user is participating in"""
        query = (
            select(ChallengeParticipant, GlobalChallenge)
            .join(GlobalChallenge, ChallengeParticipant.challenge_id == GlobalChallenge.id)
            .where(ChallengeParticipant.user_id == UUID(user_id))
            .order_by(GlobalChallenge.end_date.desc())
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        user_challenges = []
        for participant, challenge in rows:
            target = challenge.goal.get("target", 1)
            percentage = min((participant.progress / target) * 100, 100) if target > 0 else 0
            
            user_challenges.append({
                "challenge_id": str(challenge.id),
                "challenge_title": challenge.title,
                "challenge_emoji": challenge.emoji,
                "goal": challenge.goal,
                "progress": participant.progress,
                "target": target,
                "completed": participant.completed,
                "percentage": round(percentage, 1),
                "joined_at": participant.joined_at,
            })
        
        return user_challenges
