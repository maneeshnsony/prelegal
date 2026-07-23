import json
from unittest.mock import MagicMock, patch

from app.llm import NdaChatTurn, build_system_prompt, run_chat_turn
from app.models import ChatMessage, NdaFormData


def test_build_system_prompt_includes_current_field_values():
    fields = NdaFormData(partyAName="Acme Inc.", purpose="evaluating a partnership")
    prompt = build_system_prompt(fields)

    assert "Acme Inc." in prompt
    assert "evaluating a partnership" in prompt
    assert "party_a_name" in prompt
    assert "jurisdiction" in prompt


def test_run_chat_turn_parses_structured_response():
    canned_turn = NdaChatTurn(
        party_a_name="Acme Inc.",
        party_b_name="Globex Corporation",
        reply="Great, and what's the purpose of sharing information?",
    )
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content=canned_turn.model_dump_json()))
    ]

    with patch("app.llm.litellm.completion", return_value=mock_response) as mock_completion:
        result = run_chat_turn(
            history=[ChatMessage(role="assistant", content="Hi there!")],
            current_fields=NdaFormData(),
            user_message="It's Acme Inc. and Globex Corporation",
        )

    assert result.party_a_name == "Acme Inc."
    assert result.party_b_name == "Globex Corporation"
    assert "purpose" in result.reply

    call_kwargs = mock_completion.call_args.kwargs
    assert call_kwargs["response_format"] is NdaChatTurn
    messages = call_kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1] == {"role": "assistant", "content": "Hi there!"}
    assert messages[-1] == {
        "role": "user",
        "content": "It's Acme Inc. and Globex Corporation",
    }
