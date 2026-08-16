import json
from openai import OpenAI
from app.models import Change, Finding
from app.config import OPENAI_API_KEY, OPENAI_MODEL, MIN_SIGNIFICANCE_SCORE

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM = """You are AIOps Change Scout.

Your job is operational research, not content generation.

You receive observed changes from real sources. Determine whether there is a
non-obvious, useful operational finding worth publishing for DevOps, SRE,
platform engineering, observability, cloud, AIOps, or security practitioners.

Reject:
- generic explainers
- release-note summaries with no analysis
- obvious facts
- promotional content
- unsupported claims
- claims that cannot be traced to supplied evidence
- topics whose only value is that they are new

A publishable finding must explain something that happened, why it matters,
who is affected, and what an operator should understand or investigate next.

Do not invent testing, benchmarks, incidents, user reports, or source URLs.
Use only the supplied evidence.
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "publishable": {"type": "boolean"},
        "significance_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "title": {"type": "string"},
        "finding": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "affected_operators": {"type": "array", "items": {"type": "string"}},
        "evidence_urls": {"type": "array", "items": {"type": "string"}},
        "follow_up_questions": {"type": "array", "items": {"type": "string"}},
        "recommended_article_angle": {"type": "string"},
    },
    "required": [
        "publishable", "significance_score", "title", "finding",
        "why_it_matters", "affected_operators", "evidence_urls",
        "follow_up_questions", "recommended_article_angle"
    ],
    "additionalProperties": False,
}

def investigate(changes: list[Change]) -> Finding:
    payload = json.dumps([c.model_dump(mode="json") for c in changes], indent=2)
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=SYSTEM,
        input=f"""Investigate these observed changes.

{payload}

A finding should normally require at least two related pieces of evidence,
unless one primary-source change has an unusually clear operational impact.

Return only the structured finding.""",
        text={"format": {
            "type": "json_schema",
            "name": "finding",
            "strict": True,
            "schema": SCHEMA,
        }},
    )
    finding = Finding.model_validate_json(response.output_text)
    if finding.significance_score < MIN_SIGNIFICANCE_SCORE:
        finding.publishable = False
    return finding
