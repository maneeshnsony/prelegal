from app.document_types import DISCLAIMER_TEXT, render_document


def test_render_mutual_nda_substitutes_fields_and_strips_markup():
    doc = render_document(
        "Mutual-NDA",
        {
            "purpose": "evaluating a partnership",
            "effective_date": "2026-01-01",
            "party_a_name": "Acme Inc.",
            "party_b_name": "Globex Corp.",
            "mnda_term": "2 years",
            "term_of_confidentiality": "3 years",
            "governing_law": "Delaware",
            "jurisdiction": "Delaware",
        },
    )
    joined = " ".join(p["body"] for p in doc["paragraphs"])
    assert "evaluating a partnership" in joined
    assert "<span" not in joined


def test_render_sla_fills_possessive_and_bare_occurrences_with_same_value():
    doc = render_document("SLA", {"customer": "Acme Inc.", "provider": "Vendor LLC"})
    joined = " ".join(p["body"] for p in doc["paragraphs"])
    assert "Acme Inc." in joined
    assert "Acme Inc.’s" in joined


def test_render_leaves_missing_fields_as_bracketed_placeholder():
    doc = render_document("Mutual-NDA", {})
    joined = " ".join(p["body"] for p in doc["paragraphs"])
    assert "[Purpose]" in joined


def test_render_includes_disclaimer_text():
    doc = render_document("Mutual-NDA", {})
    assert doc["disclaimer"] == DISCLAIMER_TEXT
    assert "draft" in doc["disclaimer"].lower()
    assert "attorney" in doc["disclaimer"].lower()
