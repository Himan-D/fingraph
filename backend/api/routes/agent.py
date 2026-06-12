import json
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_db, AsyncSessionLocal
from db.postgres_models import Conversation, Message
from api.deps import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    symbol: Optional[str] = None


class ConversationResponse(BaseModel):
    id: int
    title: Optional[str]
    symbol: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


async def _get_or_create_conversation(
    session: AsyncSession,
    conversation_id: Optional[int],
    user_message: str,
    symbol: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Conversation:
    if conversation_id:
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv

    title = user_message[:100] + ("..." if len(user_message) > 100 else "")
    conv = Conversation(title=title, symbol=symbol, user_id=user_id)
    session.add(conv)
    await session.flush()
    return conv


async def _get_conversation_history(
    conversation_id: int,
) -> List[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .limit(50)
        )
        messages = result.scalars().all()
        return [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.content
        ]


@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(get_current_user_optional),
):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    user_id = user.get("id") if user else None

    conv = await _get_or_create_conversation(
        db, request.conversation_id, request.message, request.symbol, user_id
    )

    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)
    await db.flush()

    history = await _get_conversation_history(conv.id)
    history = history[:-1] if history else []

    system_context = None
    if request.symbol:
        system_context = f"The user is currently looking at stock symbol: {request.symbol}"

    async def event_stream():
        from core.services.agent_orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()
        full_content = ""
        tool_calls_data = []
        tool_results_data = []

        try:
            async for event in orchestrator.stream_chat(
                user_message=request.message,
                history=history,
                system_context=system_context,
                user_id=user_id,
                symbol=request.symbol,
            ):
                if event["type"] == "token":
                    full_content += event["content"]
                    data = json.dumps({"type": "token", "content": event["content"]})
                    yield f"data: {data}\n\n"

                elif event["type"] == "tool_start":
                    data = json.dumps(
                        {
                            "type": "tool_start",
                            "tool": event["tool"],
                            "args": event.get("args", {}),
                        }
                    )
                    yield f"data: {data}\n\n"

                elif event["type"] == "tool_end":
                    data = json.dumps(
                        {
                            "type": "tool_end",
                            "tool": event["tool"],
                            "result_preview": event.get("result_preview", ""),
                        }
                    )
                    yield f"data: {data}\n\n"

                elif event["type"] == "done":
                    tool_calls_data = event.get("tool_calls", [])
                    tool_results_data = event.get("tool_results", [])

            async with AsyncSessionLocal() as session:
                assistant_msg = Message(
                    conversation_id=conv.id,
                    role="assistant",
                    content=full_content,
                    tool_calls=tool_calls_data if tool_calls_data else None,
                    tool_results=tool_results_data if tool_results_data else None,
                )
                session.add(assistant_msg)
                await session.commit()

            data = json.dumps(
                {
                    "type": "done",
                    "conversation_id": conv.id,
                    "content": full_content,
                }
            )
            yield f"data: {data}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            data = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations")
async def list_conversations(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .order_by(desc(Conversation.updated_at))
        .offset(offset)
        .limit(limit)
    )
    conversations = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": c.id,
                "title": c.title,
                "symbol": c.symbol,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in conversations
        ],
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int, db: AsyncSession = Depends(get_db)
):
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    return {
        "success": True,
        "data": {
            "id": conv.id,
            "title": conv.title,
            "symbol": conv.symbol,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "tool_calls": m.tool_calls,
                    "tool_results": m.tool_results,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ],
        },
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int, db: AsyncSession = Depends(get_db)
):
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conv)
    return {"success": True, "message": "Conversation deleted"}
