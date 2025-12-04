"""AI-related Celery tasks"""
import asyncio
from typing import Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.services.ai_service import ai_service

# Import all models FIRST to avoid relationship issues
from app.models.user import User  # noqa
from app.models.category import Category  # noqa
from app.models.memory import Memory  # noqa
from app.models.embedding import Embedding  # noqa


# Sync engine for Celery tasks
sync_engine = create_engine(settings.DATABASE_URL_SYNC)
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


def run_async(coro):
    """Helper to run async functions in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="classify_memory_async")
def classify_memory_async(memory_id: str) -> Dict[str, Any]:
    """
    Background task to classify a memory
    
    Args:
        memory_id: Memory ID to classify
    
    Returns:
        Classification result
    """
    db = SyncSessionLocal()
    try:
        # Get memory
        memory = db.query(Memory).filter(Memory.id == memory_id).first()
        if not memory:
            return {"error": "Memory not found"}
        
        # Classify using AI
        result = run_async(
            ai_service.classify_memory(
                content=memory.content,
                source_type=memory.source_type.value,
                title=memory.title,
            )
        )
        
        # Find category by name
        category = db.query(Category).filter(Category.name == result.category).first()
        
        # Update memory with classification
        if category:
            memory.category_id = category.id
        memory.ai_confidence = result.confidence
        memory.memory_metadata = result.extracted_data
        
        # Generate tags
        tags = run_async(ai_service.generate_tags(memory.content))
        memory.tags = tags
        
        db.commit()
        
        return {
            "memory_id": str(memory_id),
            "category": result.category,
            "confidence": result.confidence,
            "tags": tags,
        }
    
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="generate_embedding_async")
def generate_embedding_async(memory_id: str) -> Dict[str, Any]:
    """
    Background task to generate embedding for a memory
    
    Args:
        memory_id: Memory ID
    
    Returns:
        Embedding generation result
    """
    db = SyncSessionLocal()
    try:
        # Get memory
        memory = db.query(Memory).filter(Memory.id == memory_id).first()
        if not memory:
            return {"error": "Memory not found"}
        
        # Generate embedding
        text_to_embed = f"{memory.title}\n\n{memory.content}"
        embedding_vector = run_async(ai_service.generate_embedding(text_to_embed))
        
        # Check if embedding already exists
        existing = db.query(Embedding).filter(Embedding.memory_id == memory_id).first()
        
        if existing:
            # Update existing
            existing.embedding = embedding_vector
        else:
            # Create new
            new_embedding = Embedding(
                memory_id=memory_id,
                embedding=embedding_vector,
            )
            db.add(new_embedding)
        
        db.commit()
        
        return {
            "memory_id": str(memory_id),
            "embedding_dim": len(embedding_vector),
        }
    
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="process_memory_full")
def process_memory_full(memory_id: str) -> Dict[str, Any]:
    """
    Full processing pipeline for a memory:
    1. Classify
    2. Generate embedding
    
    Args:
        memory_id: Memory ID
    
    Returns:
        Processing result
    """
    # First classify
    classification_result = classify_memory_async(memory_id)
    
    if "error" in classification_result:
        return classification_result
    
    # Then generate embedding
    embedding_result = generate_embedding_async(memory_id)
    
    return {
        "memory_id": str(memory_id),
        "classification": classification_result,
        "embedding": embedding_result,
    }


@celery_app.task(name="generate_embeddings_batch")
def generate_embeddings_batch(memory_ids: list) -> Dict[str, Any]:
    """
    Batch process embeddings for multiple memories
    
    Args:
        memory_ids: List of memory IDs
    
    Returns:
        Batch processing result
    """
    results = []
    errors = []
    
    for memory_id in memory_ids:
        try:
            result = generate_embedding_async(memory_id)
            if "error" in result:
                errors.append({"memory_id": memory_id, "error": result["error"]})
            else:
                results.append(result)
        except Exception as e:
            errors.append({"memory_id": memory_id, "error": str(e)})
    
    return {
        "processed": len(results),
        "errors": len(errors),
        "results": results,
        "error_details": errors,
    }

