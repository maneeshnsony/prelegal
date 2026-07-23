from unittest.mock import MagicMock, patch

from app.llm import IntakeTurn, run_intake_turn


def test_intake_turn_sets_document_type_on_clear_match():
    canned = IntakeTurn(document_type="Mutual-NDA", suggested_document_type=None, reply="Great, let's set up your NDA.")
    mock_response = MagicMock(choices=[MagicMock(message=MagicMock(content=canned.model_dump_json()))])
    with patch("app.llm.litellm.completion", return_value=mock_response) as mock_completion:
        result = run_intake_turn(history=[], user_message="I need an NDA")
    assert result.document_type == "Mutual-NDA"
    assert mock_completion.call_args.kwargs["response_format"] is IntakeTurn


def test_intake_turn_suggests_closest_match_without_setting_document_type():
    canned = IntakeTurn(
        document_type=None,
        suggested_document_type="Software-License-Agreement",
        reply="We don't generate employment contracts, but a Software License Agreement might fit — want to use that?",
    )
    mock_response = MagicMock(choices=[MagicMock(message=MagicMock(content=canned.model_dump_json()))])
    with patch("app.llm.litellm.completion", return_value=mock_response):
        result = run_intake_turn(history=[], user_message="I need an employment contract")
    assert result.document_type is None
    assert result.suggested_document_type == "Software-License-Agreement"
