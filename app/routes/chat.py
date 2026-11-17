import logging
import json
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.ai.chat import chat_service

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="Question to ask about Virat Kohli",
        example="How many international centuries has Virat Kohli scored?"
    )


class ChatResponse(BaseModel):
    answer: str = Field(
        ...,
        description="Complete final answer text",
        example="Virat Kohli has scored 80 international centuries."
    )


@router.post("/llm", response_model=ChatResponse)
async def chat(request: Optional[ChatRequest] = None, prompt: Optional[str] = Query(None)):
    """
    Accepts prompts via JSON body: {"prompt": "..."}
    or as query parameter: /llm?prompt=...
    Returns the complete final answer as a single response after generation is finished.
    """
    user_prompt = (request.prompt if request else None) or prompt

    if not user_prompt or not user_prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    try:
        answer = await chat_service.chat(user_prompt.strip())
        return ChatResponse(answer=answer)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate an answer. Please try again later."
        )
@router.post("/llm/stream")
async def chat_stream(
    request: Optional[ChatRequest] = None,
    prompt: Optional[str] = Query(None)):
    user_prompt = (request.prompt if request else None) or prompt

    if not user_prompt or not user_prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty."
        )

    async def event_generator():
        try:
            async for chunk in chat_service.stream_chat(
                user_prompt.strip()
            ):
                yield f"data: {json.dumps({'token': chunk})}\n\n"

            yield "event: done\ndata: {}\n\n"

        except Exception:
            logger.exception("SSE streaming failed.")

            yield (
                "event: error\n"
                'data: {"message":"Failed to generate response."}\n\n'
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
