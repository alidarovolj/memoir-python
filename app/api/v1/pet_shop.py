"""
Pet Shop API endpoints

Routes:
- GET /api/v1/pets/shop - Get shop catalog
- POST /api/v1/pets/shop/buy - Purchase item
- POST /api/v1/pets/shop/equip - Equip/unequip item
- GET /api/v1/pets/inventory - Get user's inventory
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.pet_shop import (
    PetItemResponse,
    UserPetItemResponse,
    PurchaseItemRequest,
    EquipItemRequest,
)
from app.services.pet_shop_service import PetShopService

router = APIRouter()


@router.get("/shop", response_model=List[PetItemResponse])
async def get_shop(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get pet shop catalog with all available items
    
    Shows which items are unlocked, owned, and equipped
    """
    try:
        items = await PetShopService.get_shop_items(db, str(current_user.id))
        return items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get shop: {str(e)}"
        )


@router.post("/shop/buy")
async def buy_item(
    request: PurchaseItemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Purchase an item from the shop
    
    Requires enough XP and unlock requirements to be met
    """
    try:
        result = await PetShopService.purchase_item(
            db,
            str(current_user.id),
            request.item_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purchase item: {str(e)}"
        )


@router.post("/shop/equip")
async def equip_item(
    request: EquipItemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Equip or unequip an owned item
    
    Only one item of each type can be equipped at a time
    """
    try:
        result = await PetShopService.equip_item(
            db,
            str(current_user.id),
            request.item_id,
            request.equipped,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to equip item: {str(e)}"
        )


@router.get("/inventory", response_model=List[UserPetItemResponse])
async def get_inventory(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's pet inventory (owned items)
    """
    try:
        items = await PetShopService.get_user_inventory(db, str(current_user.id))
        return items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get inventory: {str(e)}"
        )
