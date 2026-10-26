# Agentic GRC: User Access Review

A minimal, real implementation of a User Access Review agent, built to [the Agentic GRC Standard](https://agenticgrc.io/standard/). Not a demo of what an agent could do, a working agent, with every principle it claims to follow visible in the code that enforces it, not just in a prompt.

## What it does

Reads an AWS IAM access export, classifies each access grant's privilege level and whether the role fits the user's department, applies deterministic rules to decide what gets flagged, and produces a review report with the actual decision left blank for a named human reviewer.

## Why this maps to the Standard, not just loosely inspired by it

| Standard principle | Where it's enforced |
|---|---|
| 2. You read. The human decides. | `classify.py` forces Claude's response through a fixed tool schema (`tool_choice`), it cannot return free text. `rules.py` never calls the model: plain Python decides the verdict. |
| 1. Determinism is engineered, not assumed | `runlog.py` logs every classification with model and timestamp. `review.py replay` reprints a past run from the log, zero model calls. |
| 4. You do not sign off. You surface the decision. | `report.py` always leaves the reviewer-decision column blank. Nothing in this repo revokes access. |
| 6. Ground answers in structured knowledge, not recall | The classification taxonomy (`models.py`) is closed: `read-only`, `service-scoped-write`, `full-admin`, `unknown`. The model cannot invent a new category even if it wanted to, the tool schema doesn't allow it. |

## Running it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key-here

python review.py review --input sample_data/aws_iam_sample.csv --connector aws
```

Prints a markdown report and logs the full run to `runs/<timestamp>.jsonl`.

To reprint a past run without calling the model again:

```bash
python review.py replay --run runs/20261026T120000Z.jsonl
```

## The sample data

`sample_data/aws_iam_sample.csv` is shaped like `aws iam generate-credential-report`, with one addition real credential reports don't carry: a role/policy column, since an access review needs to know what access someone has, not just when they last used it. A real pipeline would join this against `list-attached-user-policies`; the sample includes it directly so the demo runs from one file with no AWS account required.

The dates are fixed, not generated relative to "now." Run this long enough after late October 2026 and most records will eventually show as stale, that's expected drift of a static fixture, not a bug. Regenerate the sample with current dates if you want fresher output.

## Adding Azure or GCP

Everything in this repo except `access_review/connectors/aws.py` is provider-agnostic. Implement `Connector` (`access_review/connectors/base.py`) for Entra ID or GCP Cloud IAM, normalise into `AccessRecord`, and register it in `review.py`'s `CONNECTORS` dict. Classification, rules, logging, and reporting don't change.

## License

MIT. See [LICENSE](./LICENSE).

---

Part of [Agentic GRC](https://agenticgrc.io). See [the manifesto](https://agenticgrc.io/) and [the Standard](https://agenticgrc.io/standard/) this agent is built to.
