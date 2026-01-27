"""Messages API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload
from typing import List, Dict, Optional
from datetime import datetime
import json
from uuid import UUID

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.message import Message
from app.models.friendship import Friendship, FriendshipStatus
from app.schemas.message import MessageCreate, MessageOut, MessageListResponse, WebSocketMessage

router = APIRouter()

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        # Dictionary to store active connections: {user_id: [websocket1, websocket2, ...]}
        self.active_connections: Dict[UUID, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: UUID):
        # Note: websocket.accept() should be called before calling this method
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: UUID):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: UUID):
        """Send message to specific user"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass  # Connection might be closed
    
    async def broadcast(self, message: dict, exclude_user_id: UUID = None):
        """Broadcast message to all connected users except exclude_user_id"""
        for user_id, connections in self.active_connections.items():
            if exclude_user_id and user_id == exclude_user_id:
                continue
            for connection in connections:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: UUID,
):
    """
    WebSocket endpoint for real-time messaging
    Requires authentication token in query params: ?token=...
    """
    print(f"🔌 [WebSocket] New connection attempt for user {user_id}")
    
    # Get token from query params
    token = websocket.query_params.get("token")
    print(f"🔑 [WebSocket] Token from query: {'present' if token else 'missing'}")
    
    await websocket.accept()
    print(f"✅ [WebSocket] Connection accepted for user {user_id}")
    
    # Verify token if provided
    if token:
        from app.core.security import decode_token
        payload = decode_token(token)
        if payload is None:
            print(f"❌ [WebSocket] Invalid token for user {user_id}")
            await websocket.close(code=4001, reason="Invalid token")
            return
        token_user_id = payload.get("sub")
        if str(token_user_id) != str(user_id):
            print(f"❌ [WebSocket] User ID mismatch: token={token_user_id}, path={user_id}")
            await websocket.close(code=4003, reason="User ID mismatch")
            return
        print(f"✅ [WebSocket] Token verified for user {user_id}")
    else:
        print(f"⚠️ [WebSocket] No token provided for user {user_id}, allowing connection anyway")
    
    await manager.connect(websocket, user_id)
    print(f"✅ [WebSocket] User {user_id} added to connection manager")
    
    # Send connection confirmation
    try:
        await websocket.send_json({
            "type": "connected",
            "user_id": str(user_id)
        })
        print(f"✅ [WebSocket] Connection confirmation sent to user {user_id}")
    except Exception as e:
        print(f"⚠️ [WebSocket] Failed to send connection confirmation: {e}")
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"📨 [WebSocket] Received data from user {user_id}: {data[:100]}")
            message_data = json.loads(data)
            ws_message = WebSocketMessage(**message_data)
            
            # Get database session for each message
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                if ws_message.type == "send":
                    print(f"📤 [WebSocket] Processing send message from {user_id} to {ws_message.receiver_id}")
                    try:
                        # Create and save message
                        message = Message(
                            sender_id=user_id,
                            receiver_id=ws_message.receiver_id,
                            content=ws_message.content
                        )
                        db.add(message)
                        await db.commit()
                        await db.refresh(message)
                        print(f"✅ [WebSocket] Message saved: {message.id}")
                        
                        # Load sender info
                        sender_result = await db.execute(
                            select(User).where(User.id == user_id)
                        )
                        sender = sender_result.scalar_one_or_none()
                        
                        # Send to receiver
                        message_dict = {
                            "type": "message",
                            "message": {
                                "id": str(message.id),
                                "sender_id": str(message.sender_id),
                                "receiver_id": str(message.receiver_id),
                                "content": message.content,
                                "is_read": message.is_read,
                                "read_at": message.read_at.isoformat() if message.read_at else None,
                                "created_at": message.created_at.isoformat(),
                                "updated_at": message.updated_at.isoformat(),
                                "sender": {
                                    "id": str(sender.id),
                                    "username": sender.username,
                                    "first_name": sender.first_name,
                                    "last_name": sender.last_name,
                                    "avatar_url": sender.avatar_url,
                                } if sender else None
                            }
                        }
                        
                        # Send to receiver
                        await manager.send_personal_message(message_dict, ws_message.receiver_id)
                        print(f"✅ [WebSocket] Message sent to receiver {ws_message.receiver_id}")
                        
                        # Also send to sender so they see their own message
                        await manager.send_personal_message(message_dict, user_id)
                        print(f"✅ [WebSocket] Message sent to sender {user_id}")
                        
                        # Confirm to sender
                        await manager.send_personal_message({
                            "type": "message_sent",
                            "message_id": str(message.id)
                        }, user_id)
                        print(f"✅ [WebSocket] Confirmation sent to sender")
                    except Exception as e:
                        print(f"❌ [WebSocket] Error processing send message: {e}")
                        import traceback
                        traceback.print_exc()
                        await manager.send_personal_message({
                            "type": "error",
                            "message": str(e)
                        }, user_id)
                
                elif ws_message.type == "read":
                    # Mark message as read
                    if ws_message.message_id:
                        try:
                            result = await db.execute(
                                select(Message).where(
                                    and_(
                                        Message.id == ws_message.message_id,
                                        Message.receiver_id == user_id
                                    )
                                )
                            )
                            message = result.scalar_one_or_none()
                            if message:
                                message.is_read = True
                                message.read_at = datetime.utcnow()
                                await db.commit()
                        except Exception as e:
                            print(f"❌ [WebSocket] Error marking message as read: {e}")
                
                elif ws_message.type == "typing":
                    # Forward typing indicator to receiver
                    await manager.send_personal_message({
                        "type": "typing",
                        "sender_id": str(user_id),
                        "is_typing": True
                    }, ws_message.receiver_id)
        
    except WebSocketDisconnect:
        print(f"🔌 [WebSocket] User {user_id} disconnected")
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"❌ [WebSocket] Error for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        manager.disconnect(websocket, user_id)


@router.post("/send", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to a friend (REST API endpoint)
    This is a fallback when WebSocket is not available
    """
    # Verify friendship
    friendship_result = await db.execute(
        select(Friendship).where(
            and_(
                Friendship.status == FriendshipStatus.ACCEPTED,
                or_(
                    and_(Friendship.requester_id == current_user.id, Friendship.addressee_id == message_data.receiver_id),
                    and_(Friendship.requester_id == message_data.receiver_id, Friendship.addressee_id == current_user.id)
                )
            )
        )
    )
    friendship = friendship_result.scalar_one_or_none()
    
    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only message your friends"
        )
    
    # Create and save message
    message = Message(
        sender_id=current_user.id,
        receiver_id=message_data.receiver_id,
        content=message_data.content
    )
    db.add(message)
    await db.commit()
    
    # Load message with sender relationship
    result = await db.execute(
        select(Message)
        .where(Message.id == message.id)
        .options(selectinload(Message.sender))
    )
    message = result.scalar_one()
    
    print(f"✅ [REST API] Message saved: {message.id} from {current_user.id} to {message_data.receiver_id}")
    
    return MessageOut.from_orm(message)


@router.get("/{friend_id}", response_model=MessageListResponse)
async def get_messages(
    friend_id: UUID,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get message history with a friend
    """
    # Verify friendship
    friendship_result = await db.execute(
        select(Friendship).where(
            and_(
                Friendship.status == FriendshipStatus.ACCEPTED,
                or_(
                    and_(Friendship.requester_id == current_user.id, Friendship.addressee_id == friend_id),
                    and_(Friendship.requester_id == friend_id, Friendship.addressee_id == current_user.id)
                )
            )
        )
    )
    friendship = friendship_result.scalar_one_or_none()
    
    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only message your friends"
        )
    
    # Get messages
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Message)
        .where(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == friend_id),
                and_(Message.sender_id == friend_id, Message.receiver_id == current_user.id)
            )
        )
        .order_by(desc(Message.created_at))
        .limit(page_size)
        .offset(offset)
        .options(selectinload(Message.sender), selectinload(Message.receiver))
    )
    messages = result.scalars().all()
    
    # Get total count
    count_result = await db.execute(
        select(func.count(Message.id)).where(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == friend_id),
                and_(Message.sender_id == friend_id, Message.receiver_id == current_user.id)
            )
        )
    )
    total = count_result.scalar()
    
    return MessageListResponse(
        messages=[MessageOut.from_orm(msg) for msg in messages],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/read/{message_id}")
async def mark_message_as_read(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a message as read
    """
    result = await db.execute(
        select(Message).where(
            and_(
                Message.id == message_id,
                Message.receiver_id == current_user.id
            )
        )
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    message.is_read = True
    message.read_at = datetime.utcnow()
    await db.commit()
    
    return {"success": True}
