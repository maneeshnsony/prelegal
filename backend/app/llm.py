from pathlib import Path
from typing import Literal, Optional

import litellm
from dotenv import load_dotenv
from pydantic import BaseModel

from app.document_types import DOCUMENT_TYPES, build_field_turn_model, build_field_turn_system_prompt
from app.models import ChatMessage

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}

_SLUGS = tuple(DOCUMENT_TYPES.keys())
_SlugLiteral = Literal[_SLUGS]  # type: ignore[valid-type]


class IntakeTurn(BaseModel):
    document_type: Optional[_SlugLiteral] = None
    suggested_document_type: Optional[_SlugLiteral] = None
    reply: str


def build_intake_system_prompt() -> str:
    catalog_list = "\n".join(
        f"- {slug}: {schema.description}" for slug, schema in DOCUMENT_TYPES.items()
    )
    return f"""You are a legal-intake assistant. We can generate exactly these document types:
{catalog_list}

Instructions:
- Figure out which document type the user wants.
- If it clearly matches one of the above, set document_type to that slug and confirm with the user.
- If it does NOT match any of the above, do NOT set document_type. Instead explain we can't \
generate that exact document, and set suggested_document_type to the closest available match \
so the user can confirm they'd like to proceed with it.
- Only set document_type once the user has explicitly confirmed — either their initial request \
matched directly, or they confirmed your suggested_document_type in a follow-up message.
- Keep replies concise and conversational.
"""


def run_intake_turn(history: list[ChatMessage], user_message: str) -> IntakeTurn:
    messages = [{"role": "system", "content": build_intake_system_prompt()}]
    messages.extend({"role": m.role, "content": m.content} for m in history)
    messages.append({"role": "user", "content": user_message})

    response = litellm.completion(
        model=MODEL,
        messages=messages,
        reasoning_effort="low",
        extra_body=EXTRA_BODY,
        response_format=IntakeTurn,
    )
    return IntakeTurn.model_validate_json(response.choices[0].message.content)


def run_field_turn(
    slug: str, history: list[ChatMessage], current_fields: dict[str, str], user_message: str
) -> BaseModel:
    Model = build_field_turn_model(slug)
    messages = [{"role": "system", "content": build_field_turn_system_prompt(slug, current_fields)}]
    messages.extend({"role": m.role, "content": m.content} for m in history)
    messages.append({"role": "user", "content": user_message})

    response = litellm.completion(
        model=MODEL,
        messages=messages,
        reasoning_effort="low",
        extra_body=EXTRA_BODY,
        response_format=Model,
    )
    return Model.model_validate_json(response.choices[0].message.content)
