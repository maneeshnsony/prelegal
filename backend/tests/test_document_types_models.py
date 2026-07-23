from app.document_types import build_field_turn_model, build_field_turn_system_prompt


def test_build_field_turn_model_has_all_fields_plus_reply():
    Model = build_field_turn_model("Mutual-NDA")
    instance = Model(reply="hi")
    assert instance.party_a_name == ""
    assert instance.reply == "hi"


def test_build_field_turn_model_is_cached():
    assert build_field_turn_model("SLA") is build_field_turn_model("SLA")


def test_system_prompt_includes_title_and_known_values():
    prompt = build_field_turn_system_prompt("SLA", {"target_uptime": "99.9%"})
    assert "SLA" in prompt
    assert "99.9%" in prompt
    assert "target_uptime" in prompt
