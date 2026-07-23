import json
from pathlib import Path

from app.document_types import DOCUMENT_TYPES, slugify_label


def test_all_catalog_entries_have_a_parsed_schema():
    catalog = json.loads((Path(__file__).resolve().parents[2] / "catalog.json").read_text())
    for entry in catalog:
        slug = entry["filename"].removesuffix(".md")
        assert slug in DOCUMENT_TYPES
        assert len(DOCUMENT_TYPES[slug].fields) > 0


def test_mutual_nda_matches_current_eight_fields():
    field_ids = [f.field_id for f in DOCUMENT_TYPES["Mutual-NDA"].fields]
    assert field_ids == [
        "party_a_name", "party_b_name", "purpose", "effective_date",
        "mnda_term", "term_of_confidentiality", "governing_law", "jurisdiction",
    ]


def test_possessive_labels_collapse_to_same_field_id():
    fields = {f.field_id: f.label for f in DOCUMENT_TYPES["SLA"].fields}
    assert "customer" in fields
    assert "customers" not in fields
    assert "provider" in fields


def test_slugify_strips_possessive_suffix():
    assert slugify_label("Customer’s") == "customer"
    assert slugify_label("Customer's") == "customer"
    assert slugify_label("Target Uptime") == "target_uptime"
