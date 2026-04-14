"""
OpenResponses-compatible webhook endpoint for OpenClaw integration.

POST /v1/responses -- receives messages from OpenClaw, routes through Suhird handler,
returns OpenResponses-formatted JSON.
"""
import logging
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.handler import handle_message
from src.config import settings
from src.database import get_db

logger = logging.getLogger("suhird.webhook")

router = APIRouter()


def _extract_phone_and_message(body: dict) -> tuple[str, str]:
    """
    Extract sender phone and message text from an OpenResponses request.

    OpenClaw may send the payload in various formats:
    - Direct: {"input": "hello", "metadata": {"from": "+91..."}}
    - Wrapped: {"body": {"input": "hello", "metadata": {"from": "+91..."}}}
    - Input as list: {"input": [{"role": "user", "content": [{"type": "input_text", "text": "hello"}]}]}
    """
    # Unwrap if nested
    if "body" in body and isinstance(body["body"], dict):
        body = body["body"]

    # Extract phone from metadata
    metadata = body.get("metadata", {})
    phone = metadata.get("from", "")
    if not phone:
        phone = metadata.get("sender", "")
    if not phone:
        phone = metadata.get("phone", "")

    # Extract message text
    raw_input = body.get("input", "")

    if isinstance(raw_input, str):
        message = raw_input
    elif isinstance(raw_input, list):
        # OpenResponses message array format
        message = ""
        for item in raw_input:
            if isinstance(item, dict):
                if item.get("role") == "user":
                    content = item.get("content", [])
                    if isinstance(content, str):
                        message = content
                    elif isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("type") in ("input_text", "text"):
                                message = c.get("text", "")
                                break
                elif isinstance(item.get("text"), str):
                    message = item["text"]
            elif isinstance(item, str):
                message = item
            if message:
                break
    else:
        message = str(raw_input)

    return phone, message.strip()


@router.post("/v1/responses")
async def openclaw_responses(request: Request, db: AsyncSession = Depends(get_db)):
    """OpenResponses API endpoint for OpenClaw integration."""
    # Verify token
    auth = request.headers.get("authorization", "")
    expected = f"Bearer {settings.suhird_api_token}"
    if auth != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = await request.json()
    phone, message = _extract_phone_and_message(body)

    if not phone:
        raise HTTPException(status_code=400, detail="Missing sender phone in metadata")

    # Check if this is a known number (should not reach here, but guard anyway)
    if phone in settings.all_known_numbers:
        return _build_response("This number is handled by the main assistant.", response_id=str(uuid.uuid4()))

    logger.info("Incoming message from %s: %s", phone[:6] + "***", message[:50])

    redis_client = request.app.state.redis
    response_text = await handle_message(phone, message, redis_client, db)

    return _build_response(response_text, response_id=str(uuid.uuid4()))


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Alternative plain webhook endpoint for direct integration.
    Expects: {"from": "+91...", "message": "hello"}
    """
    body = await request.json()
    phone = body.get("from", "")
    message = body.get("message", "")

    if not phone:
        raise HTTPException(status_code=400, detail="Missing 'from' field")

    if phone in settings.all_known_numbers:
        return {"status": "skipped", "reason": "known number"}

    redis_client = request.app.state.redis
    response_text = await handle_message(phone, message, redis_client, db)

    return {"status": "ok", "response": response_text}


def _build_response(text: str, response_id: str) -> dict:
    """Build OpenResponses-formatted JSON response."""
    return {
        "id": response_id,
        "object": "response",
        "status": "completed",
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {"type": "output_text", "text": text}
                ],
            }
        ],
        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        },
    }
