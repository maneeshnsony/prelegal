import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, create_model

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "templates"
CATALOG_PATH = REPO_ROOT / "catalog.json"
OVERRIDES_PATH = Path(__file__).resolve().parent / "document_type_overrides.json"

SPAN_RE = re.compile(r'<span\s+class="([a-z_]+)"[^>]*>([^<]+)</span>', re.IGNORECASE)
POSSESSIVE_RE = re.compile(r"[’']s$")

DISCLAIMER_TEXT = (
    "This document was generated with AI assistance and is provided as a draft only. "
    "It does not constitute legal advice and should be reviewed by a qualified attorney "
    "before use or execution."
)


@dataclass
class FieldSpec:
    field_id: str
    label: str


@dataclass
class SpanOccurrence:
    span_class: str
    raw_label: str
    field_id: str
    is_possessive: bool


@dataclass
class DocumentTypeSchema:
    slug: str
    title: str
    description: str
    fields: list[FieldSpec] = field(default_factory=list)


def slugify_label(label: str) -> str:
    base = POSSESSIVE_RE.sub("", label.strip()).lower()
    return re.sub(r"[^a-z0-9]+", "_", base).strip("_")


def parse_template_spans(text: str) -> list[SpanOccurrence]:
    occurrences = []
    for span_class, raw_label in SPAN_RE.findall(text):
        raw_label = raw_label.strip()
        is_possessive = bool(POSSESSIVE_RE.search(raw_label))
        occurrences.append(
            SpanOccurrence(
                span_class=span_class,
                raw_label=raw_label,
                field_id=slugify_label(raw_label),
                is_possessive=is_possessive,
            )
        )
    return occurrences


def _load_catalog() -> list[dict]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _load_overrides() -> dict[str, list[dict]]:
    if not OVERRIDES_PATH.exists():
        return {}
    return json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))


def _build_schema(entry: dict, overrides: dict) -> DocumentTypeSchema:
    slug = entry["filename"].removesuffix(".md")
    text = (TEMPLATES_DIR / entry["filename"]).read_text(encoding="utf-8")
    occurrences = parse_template_spans(text)

    fields: list[FieldSpec] = []
    seen: set[str] = set()

    # Cover-page override fields (e.g. NDA party names) precede body-derived
    # fields, since they conceptually belong on the cover page.
    for extra in overrides.get(slug, []):
        if extra["field_id"] not in seen:
            seen.add(extra["field_id"])
            fields.append(FieldSpec(**extra))

    for occ in occurrences:
        if occ.field_id in seen:
            continue
        seen.add(occ.field_id)
        label = occ.raw_label[:-2] if occ.is_possessive else occ.raw_label
        fields.append(FieldSpec(field_id=occ.field_id, label=label.strip()))

    return DocumentTypeSchema(
        slug=slug,
        title=slug.replace("-", " "),
        description=entry["description"],
        fields=fields,
    )


def _build_all() -> dict[str, DocumentTypeSchema]:
    overrides = _load_overrides()
    schemas: dict[str, DocumentTypeSchema] = {}
    for entry in _load_catalog():
        slug = entry["filename"].removesuffix(".md")
        schemas[slug] = _build_schema(entry, overrides)
    return schemas


DOCUMENT_TYPES: dict[str, DocumentTypeSchema] = _build_all()


def _model_class_name(slug: str) -> str:
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", slug) if p]
    return "".join(p.capitalize() for p in parts) + "FieldTurn"


@lru_cache(maxsize=None)
def build_field_turn_model(slug: str) -> type[BaseModel]:
    schema = DOCUMENT_TYPES[slug]
    field_definitions: dict = {f.field_id: (str, "") for f in schema.fields}
    field_definitions["reply"] = (str, ...)
    return create_model(_model_class_name(slug), **field_definitions)


def build_field_turn_system_prompt(slug: str, known_values: dict[str, str]) -> str:
    schema = DOCUMENT_TYPES[slug]
    field_list = "\n".join(f"- {f.field_id} ({f.label})" for f in schema.fields)
    return f"""You are a legal-intake assistant helping a user fill out a {schema.title} \
through natural conversation.

{schema.description}

This document needs the following fields:
{field_list}

Current known field values (JSON, empty string means not yet known):
{json.dumps(known_values)}

Instructions:
- Have a natural conversation. You may ask about more than one related field at a \
time, but do not interrogate the user with a rigid one-field-at-a-time checklist.
- Only fill in a field when the user's message clearly supplies or updates it. \
Never fabricate or guess a value.
- If the user's answer is ambiguous or incomplete, ask a clarifying follow-up and \
leave that field unchanged.
- Always return ALL fields, carrying forward every previously known value unless \
the latest message clearly changes it.
- Once every field is known, confirm this with the user and let them know they \
can now download the completed document.
- Keep replies concise and conversational.
"""


def render_document(slug: str, fields: dict[str, str]):
    schema = DOCUMENT_TYPES[slug]
    text = (TEMPLATES_DIR / f"{slug}.md").read_text(encoding="utf-8")

    def _replace(match: re.Match) -> str:
        raw_label = match.group(2).strip()
        is_possessive = bool(POSSESSIVE_RE.search(raw_label))
        value = fields.get(slugify_label(raw_label), "")
        if not value:
            return f"[{raw_label}]"
        return f"{value}’s" if is_possessive else value

    filled = SPAN_RE.sub(_replace, text)
    paragraphs = []
    for line in filter(None, filled.split("\n")):
        m = re.match(r"^(\d+)\.\s+\*\*(.+?)\*\*\.\s*(.*)$", line)
        if m:
            paragraphs.append({"number": int(m.group(1)), "title": m.group(2), "body": m.group(3)})
        else:
            paragraphs.append({"number": 0, "title": "", "body": line})

    cover_fields = [
        {"field_id": f.field_id, "label": f.label, "value": fields.get(f.field_id, "")}
        for f in schema.fields
    ]
    return {
        "document_type": slug,
        "title": schema.title,
        "cover_fields": cover_fields,
        "paragraphs": paragraphs,
        "disclaimer": DISCLAIMER_TEXT,
    }
