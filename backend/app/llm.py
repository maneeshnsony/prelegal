import json
from pathlib import Path

import litellm
from dotenv import load_dotenv
from pydantic import BaseModel

from app.models import ChatMessage, NdaFormData

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}

# (field name on NdaChatTurn/nda_drafts, human label, purpose shown to the LLM)
FIELD_DESCRIPTIONS = [
    ("party_a_name", "Party A Name", "the legal name of the first party to the NDA"),
    ("party_b_name", "Party B Name", "the legal name of the second party to the NDA"),
    (
        "effective_date",
        "Effective Date",
        "the date the NDA takes effect",
    ),
    (
        "purpose",
        "Purpose",
        "why the parties are sharing confidential information with each other",
    ),
    (
        "mnda_term",
        "MNDA Term",
        "how long the agreement itself lasts before it expires",
    ),
    (
        "term_of_confidentiality",
        "Term of Confidentiality",
        "how long confidentiality obligations survive after the agreement ends",
    ),
    (
        "governing_law",
        "Governing Law",
        "the state/jurisdiction whose law governs the agreement",
    ),
    (
        "jurisdiction",
        "Jurisdiction",
        "where legal disputes about the agreement must be litigated",
    ),
]


class NdaChatTurn(BaseModel):
    party_a_name: str = ""
    party_b_name: str = ""
    effective_date: str = ""
    purpose: str = ""
    mnda_term: str = ""
    term_of_confidentiality: str = ""
    governing_law: str = ""
    jurisdiction: str = ""
    reply: str


def nda_chat_turn_to_form_data(turn: NdaChatTurn) -> NdaFormData:
    return NdaFormData(
        partyAName=turn.party_a_name,
        partyBName=turn.party_b_name,
        effectiveDate=turn.effective_date,
        purpose=turn.purpose,
        mndaTerm=turn.mnda_term,
        termOfConfidentiality=turn.term_of_confidentiality,
        governingLaw=turn.governing_law,
        jurisdiction=turn.jurisdiction,
    )


def build_system_prompt(current_fields: NdaFormData) -> str:
    field_list = "\n".join(
        f"- {snake_name} ({label}): {purpose}"
        for snake_name, label, purpose in FIELD_DESCRIPTIONS
    )
    known_values = {
        snake_name: getattr(current_fields, camel_name)
        for snake_name, camel_name in zip(
            (f[0] for f in FIELD_DESCRIPTIONS),
            (
                "partyAName",
                "partyBName",
                "effectiveDate",
                "purpose",
                "mndaTerm",
                "termOfConfidentiality",
                "governingLaw",
                "jurisdiction",
            ),
        )
    }

    return f"""You are a legal-intake assistant helping a user fill out a Mutual \
Non-Disclosure Agreement (MNDA) through natural conversation.

The MNDA needs the following 8 fields:
{field_list}

Current known field values (JSON, empty string means not yet known):
{json.dumps(known_values)}

Instructions:
- Have a natural conversation. You may ask about more than one related field at a \
time (e.g. governing law and jurisdiction together), but do not interrogate the \
user with a rigid one-field-at-a-time checklist.
- Only fill in a field when the user's message clearly supplies or updates it. \
Never fabricate or guess a value.
- If the user's answer is ambiguous or incomplete, ask a clarifying follow-up and \
leave that field unchanged.
- Always return ALL 8 fields in your response, carrying forward every previously \
known value unless the latest message clearly changes it.
- Once all 8 fields are known, confirm this with the user and let them know they \
can now download the completed NDA.
- Keep replies concise and conversational.
"""


def run_chat_turn(
    history: list[ChatMessage], current_fields: NdaFormData, user_message: str
) -> NdaChatTurn:
    messages = [{"role": "system", "content": build_system_prompt(current_fields)}]
    messages.extend({"role": m.role, "content": m.content} for m in history)
    messages.append({"role": "user", "content": user_message})

    response = litellm.completion(
        model=MODEL,
        messages=messages,
        reasoning_effort="low",
        extra_body=EXTRA_BODY,
        response_format=NdaChatTurn,
    )
    return NdaChatTurn.model_validate_json(response.choices[0].message.content)
