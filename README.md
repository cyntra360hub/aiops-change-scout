# AIOps Change Scout

An autonomous research agent whose job is **not to write articles**.

Its job is to monitor real changes in the cloud-native operations ecosystem, investigate operational significance, and produce an evidence-backed article only when the work produces a publishable finding.

## Mission

> Every day, inspect what changed in Kubernetes, OpenTelemetry, and selected cloud-native projects. Investigate meaningful changes. Produce a useful operational finding. Turn the finding into an article artifact. If there is no publishable finding, do not manufacture one.

The agent is intentionally independent of `aiopscommunity-app`. It has **no code dependency, network dependency, or write access** to AiOps Community.

You manually submit the generated article to AiOps Community.

## V1 sources

- Kubernetes GitHub releases
- Kubernetes GitHub repository activity
- OpenTelemetry Collector releases
- OpenTelemetry GitHub repository activity
- CNCF blog RSS (optional)
- Configurable RSS feeds

V1 deliberately starts narrow. Add sources only when the agent demonstrates useful findings.

## Outputs

Every run creates:

```text
output/YYYY-MM-DD/
  run.json
  findings.json
  sources.json
  article.md             # only when a publishable finding exists
  article.json           # only when a publishable finding exists
```

A `run.json` is always produced, even when no article is generated.

## OpenAI

The agent uses the OpenAI Responses API for analysis and article generation. The model is configurable with `OPENAI_MODEL`; the default is `gpt-5.6`. The Responses API supports direct model calls and structured/tool workflows. See the official OpenAI API documentation.

## Daily execution

GitHub Actions runs the scout once per day.

Required repository secret:

```text
OPENAI_API_KEY
```

Optional variables:

```text
OPENAI_MODEL=gpt-5.6
MIN_SIGNIFICANCE_SCORE=70
LOOKBACK_HOURS=30
```

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# add OPENAI_API_KEY

python -m app.main
```

## Manual AiOps Community integration

The agent does **not** call AiOps Community.

After a run, inspect:

```text
output/<date>/article.md
```

Submit that article manually using the AiOps Community agent API and the agent identity you choose.

This separation is intentional:

```text
AIOps Change Scout
    |
    | research + evidence
    v
article.md
    |
    | manual submission
    v
AiOps Community
    |
    v
AiOps Community moderator
```

## Design principles

1. No finding, no article.
2. Evidence before prose.
3. Changes must be traceable to sources.
4. The model cannot invent source URLs.
5. The article must distinguish observed facts from analysis.
6. Generic explainers are not publishable findings.
7. Product promotion is not a finding.
8. A release note alone is not sufficient; the agent must identify operational implications.
9. Every claim in the article should be traceable to collected evidence.
10. The agent never modifies AiOps Community.

## What success means

The primary KPI is **useful findings**, not article count.

A good week might produce:

```text
7 runs
41 changes detected
8 investigated
2 significant findings
2 articles
```

A week with no meaningful changes may correctly produce zero articles.
