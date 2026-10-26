#!/usr/bin/env python3
"""Agentic GRC: User Access Review agent.

A minimal, real implementation of the Agentic GRC Standard's Principle 2
("you read, the human decides"): Claude classifies each access grant
against a fixed taxonomy; a deterministic rules engine, not the model,
decides whether it gets flagged; a named human reviewer makes the final
call. See https://agenticgrc.io/standard/ for the full Standard this
implements, and the README for which principle maps to which file.
"""
import argparse
import sys
from pathlib import Path

from access_review.classify import classify
from access_review.connectors.aws import AWSIAMConnector
from access_review.models import AccessRecord, Classification, ReviewVerdict
from access_review.report import render
from access_review.rules import evaluate
from access_review.runlog import append, load, new_run_path

CONNECTORS = {
    "aws": AWSIAMConnector(),
}


def cmd_review(args: argparse.Namespace) -> None:
    connector = CONNECTORS[args.connector]
    records = connector.load(Path(args.input))

    run_path = new_run_path()
    rows = []
    for record in records:
        classification = classify(record, model=args.model)
        verdict = evaluate(record, classification)
        append(run_path, record, classification, verdict, args.model)
        rows.append((record, classification, verdict))

    print(render(rows))
    flagged = sum(1 for _, _, v in rows if v.status == "FLAG")
    print(
        f"\n{flagged}/{len(rows)} flagged for review. Run logged to {run_path}",
        file=sys.stderr,
    )


def cmd_replay(args: argparse.Namespace) -> None:
    entries = load(Path(args.run))
    rows = [
        (
            AccessRecord(**e["record"]),
            Classification(**e["classification"]),
            ReviewVerdict(**e["verdict"]),
        )
        for e in entries
    ]
    print(render(rows))
    print(f"\nReplayed from {args.run}: no model calls made.", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    review = sub.add_parser(
        "review", help="Run a fresh access review against an export file"
    )
    review.add_argument("--input", required=True, help="Path to the export file")
    review.add_argument("--connector", choices=CONNECTORS.keys(), default="aws")
    review.add_argument("--model", default="claude-sonnet-5")
    review.set_defaults(func=cmd_review)

    replay = sub.add_parser(
        "replay", help="Reprint a past run from its log, with no model calls"
    )
    replay.add_argument("--run", required=True, help="Path to a runs/*.jsonl file")
    replay.set_defaults(func=cmd_replay)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
