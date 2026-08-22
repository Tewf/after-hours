"""Fail if a number written into prose no longer matches the table it came from.

    python check_quoted_numbers.py

Training writes its curves and its greedy evaluations to `results/`, and every
number in a README is typed by hand from them. Nothing connected the two, so a
sentence and the run behind it could drift apart silently, and the reader has
no way to tell which one is current.

Each claim below names the file it lives in, a pattern that must match, and the
committed CSV the pattern is built from. Move a measurement and the build says
which sentence to rewrite.

**Not everything published here is checkable yet, and the gaps are listed at the
bottom on purpose** rather than quietly omitted. A checklist that silently skips
what it cannot verify reads as full coverage when it is not.
"""

import csv
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
RESULTS = ROOT / "Flappy_Bird_CNN" / "results"

FLAPPY = "Flappy_Bird_CNN/README.md"
ROOT_EN = "README.md"
ROOT_FR = "README.fr.md"
SITE = "index.html"


def table(name):
    with open(RESULTS / name, newline="\n") as handle:
        return list(csv.DictReader(handle))


def row(rows, **where):
    found = [r for r in rows if all(r[k] == v for k, v in where.items())]
    assert len(found) == 1, f"{len(found)} rows matched {where}"
    return found[0]


def claims():
    """(what it is, regex the document must match, the documents it is in)."""
    evaluations = table("greedy_evaluations_blue.csv")
    summary = row(table("training_summary.csv"), agent="dqn")
    out = []

    # The channel-ablation table's blue column. Its greyscale column has no
    # committed run, so only the blue cell of each row is pinned: the row is
    # found by its step label and the third cell has to be the measured mean.
    labels = {"25000": "25k", "50000": "50k", "100000": "100k", "150000": "150k",
              "200000": "200k", "225000": "225k", "250000": "250k"}
    for steps, label in labels.items():
        mean = row(evaluations, environment_steps=steps)["mean_pipes"]
        out.append((f"blue channel at {label}: {mean} pipes",
                    rf"\|\s*{label}\s*\|\s*[\d.]+\s*\|\s*{re.escape(mean)}\s*\|",
                    [FLAPPY]))

    # The sentence under the table, which is the table read aloud.
    first = row(evaluations, environment_steps="50000")
    ten = row(evaluations, environment_steps="250000")
    assert int(first["best_pipes"]) >= 1, "50k no longer clears a pipe"
    assert float(ten["mean_pipes"]) >= 10, "250k no longer passes ten"
    out.append(("the blue channel clears one at 50k and passes ten at 250k",
                r"blue channel cleared one at 50k and passed ten at 250k", [FLAPPY]))

    # Wall clock, quoted on all four surfaces. The log rounds 22.6 up to 23.
    minutes = round(float(summary["training_minutes"]))
    out.append((f"training time: {summary['training_minutes']} min",
                rf"{minutes} minutes", [ROOT_EN, SITE, FLAPPY]))
    out.append((f"training time, French: {summary['training_minutes']} min",
                rf"{minutes} minutes", [ROOT_FR]))

    # Where the target was reached, quoted as an unspaced and a comma'd integer.
    steps = int(summary["target_reached_at_steps"])
    target = round(float(summary["target_pipes"]))
    out.append((f"target of {target} pipes at {steps} steps",
                rf"{target}-pipe target at {steps:,} environment steps", [FLAPPY]))
    out.append((f"best in-training evaluation: {summary['best_eval_pipes']}",
                rf"\|\s*250k\s*\|\s*[\d.]+\s*\|\s*{re.escape(summary['best_eval_pipes'])}\s*\|",
                [FLAPPY]))
    return out


# Published figures with no committed file behind them. Listed rather than
# skipped, so the coverage this file reports is the coverage it has.
UNSOURCED = [
    ("the greyscale column of the channel-ablation table, 8 values",
     "that run's log was not kept; re-running it is the only way to source it"),
    ("the 100-episode results table: mean 12.21, median 8, sd 12.63, "
     "quartiles 3 and 18, range 0 to 61, and the 99/41/23% shares",
     "eval.py --checkpoint checkpoints/dqn/best.pt --episodes 100 --seed 0 "
     "gives 11.12 +/- 10.71, min 1, max 57 on this machine, twice, "
     "deterministically. The seed or the checkpoint of the published run is "
     "not recorded, so the difference cannot be attributed from here. "
     "12.21, best 61 is also quoted on README.md, README.fr.md and index.html"),
]


def flattened(text):
    """Prose as one line, without emphasis, so a claim survives rewrapping.

    A figure that is correct but sits across a line break, or inside `**bold**`,
    is not stale and must not fail the build: this catches numbers that moved,
    not paragraphs that were reflowed.
    """
    return " ".join(text.replace("*", "").split())


def main():
    stale = []
    total = 0
    for what, pattern, documents in claims():
        for document in documents:
            total += 1
            path = ROOT / document
            if not path.exists():
                stale.append((document, pattern, f"{what}, and the file is gone"))
            elif not re.search(pattern, flattened(path.read_text())):
                stale.append((document, pattern, what))
    for document, pattern, what in stale:
        print(f"STALE  {document}: nothing matches {pattern!r} ({what})")
    if stale:
        print(f"\n{len(stale)} quoted figures no longer match their table. "
              f"Rewrite the sentence, or fix the claim in {pathlib.Path(__file__).name}.")
        return 1
    print(f"all {total} quoted figures match their tables")
    print(f"{len(UNSOURCED)} published figures have no committed source and are NOT checked:")
    for what, why in UNSOURCED:
        print(f"  - {what}\n      {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
