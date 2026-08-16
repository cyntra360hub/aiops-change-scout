import json
from openai import OpenAI
from app.models import Finding, Change, Article
from app.config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "dek": {"type": "string"},
        "body_markdown": {"type": "string"},
        "evidence_urls": {"type": "array", "items": {"type": "string"}},
        "finding_summary": {"type": "string"},
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "dek", "body_markdown", "evidence_urls", "finding_summary", "limitations"],
    "additionalProperties": False,
}

def write_article(finding: Finding, changes: list[Change]) -> Article:
    evidence = [c.model_dump(mode="json") for c in changes]
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions="""You are the reporting layer of AIOps Change Scout.

Write an evidence-backed operational report from the supplied finding and
source material.

Do not pad the article to reach a word count.
Do not write a generic introduction to the technology.
Do not repeat release notes.
Do not invent tests, metrics, customer impact, incidents, or quotes.
Clearly distinguish observed facts from analysis.
Use source URLs exactly as supplied.
The article should be useful because the investigation happened.

Structure:
# title
A concise dek
## What changed
## What we found
## Why operators should care
## What to watch next
## Sources / evidence

If evidence is insufficient, say so in limitations rather than filling gaps.
""",
        input=json.dumps({
            "finding": finding.model_dump(mode="json"),
            "observations": evidence,
        }, indent=2),
        text={"format": {
            "type": "json_schema",
            "name": "article",
            "strict": True,
            "schema": SCHEMA,
        }},
    )
    return Article.model_validate_json(response.output_text)
