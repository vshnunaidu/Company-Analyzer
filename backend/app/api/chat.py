"""Chat endpoints with streaming support."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import AsyncGenerator
import json

from app.services.vectorstore import get_vector_store
from app.services.claude import get_claude_client, ClaudeError

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    ticker: str
    message: str
    history: list[ChatMessage] = []


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream a chat response about a company."""
    ticker = request.ticker.upper()

    # Check if indexed
    store = get_vector_store()
    if not store.has_ticker(ticker):
        raise HTTPException(
            status_code=400,
            detail=f"Company {ticker} not indexed. Please index first."
        )

    # Get relevant context
    context = store.search(request.message, ticker, n_results=3)

    if not context:
        raise HTTPException(status_code=404, detail="No filing data found")

    async def generate() -> AsyncGenerator[str, None]:
        try:
            claude = get_claude_client()

            # Send sources first
            sources = [
                {"section": c["name"], "fiscal_year": c["fiscal_year"]}
                for c in context
            ]
            yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"

            # Stream the response
            history = [{"role": m.role, "content": m.content} for m in request.history]

            async for chunk in claude.chat_stream(request.message, context, history):
                yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except ClaudeError as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': f'Internal error: {str(e)}'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/")
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint (fallback)."""
    ticker = request.ticker.upper()

    store = get_vector_store()
    if not store.has_ticker(ticker):
        raise HTTPException(
            status_code=400,
            detail=f"Company {ticker} not indexed. Please index first."
        )

    context = store.search(request.message, ticker, n_results=3)

    if not context:
        raise HTTPException(status_code=404, detail="No filing data found")

    try:
        claude = get_claude_client()
        history = [{"role": m.role, "content": m.content} for m in request.history]

        response_text = ""
        async for chunk in claude.chat_stream(request.message, context, history):
            response_text += chunk

        sources = [
            {"section": c["name"], "fiscal_year": c["fiscal_year"]}
            for c in context
        ]

        return {
            "response": response_text,
            "sources": sources,
        }

    except ClaudeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# Suggested questions for the UI
SUGGESTED_QUESTIONS = [
    "What are the main risk factors for this company?",
    "Summarize the company's business model",
    "What is the company's competitive advantage?",
    "How has revenue changed year over year?",
    "What are management's key priorities?",
]


@router.get("/suggestions")
async def get_suggestions():
    """Get suggested questions for the chat."""
    return {"suggestions": SUGGESTED_QUESTIONS}
