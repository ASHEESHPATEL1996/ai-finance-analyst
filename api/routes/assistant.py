from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from agents.research_assistant import chat

router = APIRouter(prefix="/assistant", tags=["Research Assistant"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    chat_history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    success: bool
    response: str = ""
    intent: str = ""
    tool_result: Optional[dict] = None
    error: str = ""


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if len(request.message) > 1000:
        raise HTTPException(status_code=400, detail="Message cannot exceed 1000 characters")

    if len(request.chat_history) > 20:
        request.chat_history = request.chat_history[-20:]

    history = [
        {"role": msg.role, "content": msg.content}
        for msg in request.chat_history
        if msg.role in ("user", "assistant")
    ]

    result = chat(
        user_message=request.message.strip(),
        chat_history=history,
    )

    if result.get("error") and not result.get("response"):
        return ChatResponse(
            success=False,
            error=result["error"],
        )

    return ChatResponse(
        success=True,
        response=result.get("response", ""),
        intent=result.get("intent", "general_question"),
        tool_result=result.get("tool_result"),
    )


@router.get("/health", tags=["Health"])
async def assistant_health():
    return {"status": "ok", "agent": "research_assistant"}