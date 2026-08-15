"""Plot learning curves against environment steps, so different runs are comparable.

    python plot_results.py --series "REINFORCE with baseline=results/reinforce.csv" \
                           --series "DQN=results/dqn.csv" \
                           --out results/learning_curve.png

REINFORCE logs per epoch and DQN logs per step, so both are converted to
cumulative environment steps. Comparing them per update would flatter whichever
algorithm collects more experience per update.
"""

import csv
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLOURS = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]


def read_curve(path):
    """Return (cumulative steps, pipes per episode), whichever logger wrote it.

    dqn.py writes a cumulative `step` column; train.py writes a per-epoch
    `steps` column that has to be accumulated.
    """
    steps, pipes, total = [], [], 0
    with open(path) as handle:
        for row in csv.DictReader(handle):
            if "step" in row:
                steps.append(int(row["step"]))
            else:
                total += int(row["steps"])
                steps.append(total)
            pipes.append(float(row["avg_pipes"]))
    return steps, pipes


def smooth(values, window):
    """Running mean, so the curve shows the trend rather than episode noise."""
    return [sum(values[max(0, i - window + 1):i + 1]) /
            len(values[max(0, i - window + 1):i + 1]) for i in range(len(values))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--series", action="append", required=True,
                        metavar="LABEL=PATH", help="repeat once per curve")
    parser.add_argument("--out", default="results/learning_curve.png")
    parser.add_argument("--smooth", type=int, default=15)
    parser.add_argument("--target", type=float, default=10.0)
    parser.add_argument("--title", default="Flappy Bird from raw pixels")
    args = parser.parse_args()

    figure, axes = plt.subplots(figsize=(9, 5))
    for index, series in enumerate(args.series):
        label, _, path = series.partition("=")
        try:
            steps, pipes = read_curve(path)
        except FileNotFoundError:
            print(f"skipping {path}, not found")
            continue
        if not steps:
            continue
        colour = COLOURS[index % len(COLOURS)]
        axes.plot(steps, pipes, color=colour, alpha=0.18, lw=0.8)
        axes.plot(steps, smooth(pipes, args.smooth), color=colour, label=label, lw=1.9)

    axes.axhline(args.target, color="#666666", ls="--", lw=1,
                 label=f"target, {args.target:g} pipes")
    axes.set_xlabel("environment steps")
    axes.set_ylabel("pipes cleared per episode")
    axes.set_title(args.title)
    axes.legend(frameon=False)
    axes.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    figure.savefig(args.out, dpi=140)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
