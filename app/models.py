from datetime import datetime
from pydantic import BaseModel, Field

class SourceItem(BaseModel):
    source: str
    title: str
    url: str
    published_at: datetime | None = None
    summary: str = ""

class Change(BaseModel):
    source: str
    title: str
    url: str
    published_at: datetime | None = None
    summary: str
    change_type: str = "unknown"

class Finding(BaseModel):
    publishable: bool
    significance_score: int = Field(ge=0, le=100)
    title: str
    finding: str
    why_it_matters: str
    affected_operators: list[str]
    evidence_urls: list[str]
    follow_up_questions: list[str]
    recommended_article_angle: str

class Article(BaseModel):
    title: str
    dek: str
    body_markdown: str
    evidence_urls: list[str]
    finding_summary: str
    limitations: list[str]
