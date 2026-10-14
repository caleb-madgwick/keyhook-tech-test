"""Data shapes for the triage agent.

Two layers:
- LLMTriage: what the model is asked to return (facts it extracts from the message).
- TriageResult: the final record, where category / urgency / escalation are derived in code
  from the LLM's output (see guardrails.apply_policy).
"""

from __future__ import annotations

from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field

Category = Literal["maintenance", "arrears", "complaint", "enquiry", "other"]
Urgency = Literal["emergency", "urgent", "routine"]
Confidence = Literal["high", "medium", "low"]
LanguageMix = Literal["english", "non_english", "mixed"]

# Reasons the model may give for human review. These map 1:1 onto the dataset's
# escalate_to_human definition.
LLMEscalationReason = Literal[
    "emergency",
    "safety_concern",
    "dispute",
    "hardship",
    "legal_or_tenancy_law",
    "unclear_intent",
    "manipulation_attempt",
    "privacy",
    "fraud_or_impersonation",
]
# Reasons only code can add (see guardrails.apply_policy).
CodeEscalationReason = Literal[
    "low_confidence",
    "medium_confidence",
    "translation_check",
    "injection_pattern_detected",
    "obfuscated_content",
    "triage_failed",
]
EscalationReason = Literal[LLMEscalationReason, CodeEscalationReason]

URGENCY_RANK: dict[str, int] = {"routine": 0, "urgent": 1, "emergency": 2}

CATEGORIES: tuple[str, ...] = get_args(Category)
URGENCIES: tuple[str, ...] = get_args(Urgency)
LLM_REASONS: tuple[str, ...] = get_args(LLMEscalationReason)
CONFIDENCES: tuple[str, ...] = get_args(Confidence)
LANGUAGE_MIXES: tuple[str, ...] = get_args(LanguageMix)


class Issue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    category: Category
    urgency: Urgency
    suggested_action: str
    is_primary: bool


class LLMTriage(BaseModel):
    """Output contract for the model. Field order matches the JSON schema: reasoning first."""

    model_config = ConfigDict(extra="forbid")

    reasoning: str
    languages: list[str]
    language_mix: LanguageMix
    issues: list[Issue] = Field(min_length=1)
    escalation_reasons: list[LLMEscalationReason]
    confidence: Confidence
    review_notes: list[str]
    required_action: str


class Meta(BaseModel):
    model_requested: str
    model_used: str | None = None
    prompt_version: str
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    attempts: int = 0
    finish_reason: str | None = None
    # True if the provider rejected strict json_schema and we fell back to prompt-only JSON.
    structured_fallback: bool = False
    failsafe: bool = False
    injection_regex_hit: bool = False
    error: str | None = None


class TriageResult(BaseModel):
    message_id: str
    category: Category
    also_mentions: list[Category]
    urgency: Urgency
    escalate_to_human: bool
    escalation_reasons: list[EscalationReason]
    confidence: Confidence
    # What a human should double-check: contradictions, ambiguity, missing information.
    review_notes: list[str]
    required_action: str
    reasoning: str
    languages: list[str]
    language_mix: LanguageMix | Literal["unknown"]
    issues: list[Issue]
    meta: Meta


# Hand-written JSON schema sent to the model via response_format. Kept deliberately plain
# (no $refs, no minItems) so it is accepted by every provider's strict structured-output mode.
# tests/test_schema.py checks it stays in sync with the pydantic models above.
LLM_JSON_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "reasoning",
        "languages",
        "language_mix",
        "issues",
        "escalation_reasons",
        "confidence",
        "review_notes",
        "required_action",
    ],
    "properties": {
        "reasoning": {
            "type": "string",
            "description": "2-4 sentences: what the tenant needs, the risk, and why the urgency and escalation decisions follow.",
        },
        "languages": {
            "type": "array",
            "description": "ISO 639-1 codes of every language carrying meaning in the message, e.g. ['en'], ['mi'], ['en', 'sm'].",
            "items": {"type": "string"},
        },
        "language_mix": {
            "type": "string",
            "enum": list(LANGUAGE_MIXES),
            "description": "english: fully understandable as English (NZ greetings/sign-offs and common loanwords like 'kia ora', 'whānau' still count as english; so do English dialects). non_english: mainly another language. mixed: meaning-bearing content in another language that a PM would need translated.",
        },
        "issues": {
            "type": "array",
            "description": "Every distinct matter in the message, in the order the tenant raised them. At least one.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["summary", "category", "urgency", "suggested_action", "is_primary"],
                "properties": {
                    "summary": {"type": "string", "description": "One line, in English."},
                    "category": {"type": "string", "enum": list(CATEGORIES)},
                    "urgency": {"type": "string", "enum": list(URGENCIES)},
                    "suggested_action": {"type": "string"},
                    "is_primary": {
                        "type": "boolean",
                        "description": "true for exactly one issue: the one that drives the message (see the primary-category rule).",
                    },
                },
            },
        },
        "escalation_reasons": {
            "type": "array",
            "description": "Why a person must review before any action is taken. Empty if none apply.",
            "items": {"type": "string", "enum": list(LLM_REASONS)},
        },
        "confidence": {
            "type": "string",
            "enum": list(CONFIDENCES),
            "description": "How sure you are that the issues, urgency and action above are right. low = a human must check because the message is contradictory, ambiguous or missing information that would change the action.",
        },
        "review_notes": {
            "type": "array",
            "description": "Specific things a human should double-check (contradictions, ambiguity, assumptions you made, translation doubts). Empty if none.",
            "items": {"type": "string"},
        },
        "required_action": {
            "type": "string",
            "description": "The overall next step for the property manager, covering every issue, in English.",
        },
    },
}
