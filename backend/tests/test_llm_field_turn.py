from unittest.mock import MagicMock, patch

from app.document_types import build_field_turn_model
from app.llm import run_field_turn


def test_run_field_turn_parses_structured_response():
    Model = build_field_turn_model("Mutual-NDA")
    canned = Model(party_a_name="Acme Inc.", reply="And Party B?")
    mock_response = MagicMock(choices=[MagicMock(message=MagicMock(content=canned.model_dump_json()))])
    with patch("app.llm.litellm.completion", return_value=mock_response) as mock_completion:
        result = run_field_turn("Mutual-NDA", history=[], current_fields={}, user_message="Acme Inc.")
    assert result.party_a_name == "Acme Inc."
    assert mock_completion.call_args.kwargs["response_format"] is Model
