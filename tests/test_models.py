from app.models import Finding

def test_finding_score_bounds():
    f = Finding(
        publishable=True,
        significance_score=80,
        title="x",
        finding="x",
        why_it_matters="x",
        affected_operators=["SRE"],
        evidence_urls=["https://example.com"],
        follow_up_questions=[],
        recommended_article_angle="x",
    )
    assert f.significance_score == 80
