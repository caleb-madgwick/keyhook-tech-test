"""The JSON schema sent to the model is hand-written; make sure it can't drift from the
pydantic models that validate the response."""

from triage.schema import CATEGORIES, LLM_JSON_SCHEMA, LLM_REASONS, URGENCIES, Issue, LLMTriage


def test_top_level_fields_match():
    assert list(LLM_JSON_SCHEMA["properties"]) == list(LLMTriage.model_fields)
    assert LLM_JSON_SCHEMA["required"] == list(LLMTriage.model_fields)


def test_reasoning_comes_first():
    assert next(iter(LLM_JSON_SCHEMA["properties"])) == "reasoning"


def test_issue_fields_and_enums_match():
    item = LLM_JSON_SCHEMA["properties"]["issues"]["items"]
    assert list(item["properties"]) == list(Issue.model_fields)
    assert item["required"] == list(Issue.model_fields)
    assert item["properties"]["category"]["enum"] == list(CATEGORIES)
    assert item["properties"]["urgency"]["enum"] == list(URGENCIES)
    assert LLM_JSON_SCHEMA["properties"]["escalation_reasons"]["items"]["enum"] == list(LLM_REASONS)


def test_strict_mode_requirements():
    """Strict structured outputs require every object to forbid extras and require all keys."""

    def walk(node):
        if node.get("type") == "object":
            assert node["additionalProperties"] is False
            assert set(node["required"]) == set(node["properties"])
            for child in node["properties"].values():
                walk(child)
        if node.get("type") == "array":
            walk(node["items"])

    walk(LLM_JSON_SCHEMA)
