"""Plot both learning curves against environment steps, so the two are comparable.

    python plot_results.py --out results/learning_curve.png

REINFORCE logs per epoch and DQN logs per step, so both are converted to
cumulative environment steps before plotting. Comparing them per update would
flatter whichever algorithm collects more experience per update.
"""

import csv
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def read_reinforce(path):
    """Per-epoch rows; the step column is per epoch, so accumulate it."""
    steps, pipes, total = [], [], 0
    with open(path) as handle:
        for row in csv.DictReader(handle):
            total += int(row["steps"])
            steps.append(total)
            pipes.append(float(row["avg_pipes"]))
    return steps, pipes


def read_dqn(path):
    """Per-step rows; the step column is already cumulative."""
    steps, pipes = [], []
    with open(path) as handle:
        for row in csv.DictReader(handle):
            steps.append(int(row["step"]))
            pipes.append(float(row["avg_pipes"]))
    return steps, pipes


def smooth(values, window):
    """Running mean, so the curve shows the trend rather than episode noise."""
    out = []
    for i in range(len(values)):
        chunk = values[max(0, i - window + 1):i + 1]
        out.append(sum(chunk) / len(chunk))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reinforce", default="results/reinforce.csv")
    parser.add_argument("--dqn", default="results/dqn.csv")
    parser.add_argument("--out", default="results/learning_curve.png")
    parser.add_argument("--smooth", type=int, default=25)
    parser.add_argument("--target", type=float, default=10.0)
    args = parser.parse_args()

    figure, axes = plt.subplots(figsize=(9, 5))
    for path, label, colour, reader in (
        (args.reinforce, "REINFORCE with baseline", "#1f77b4", read_reinforce),
        (args.dqn, "DQN", "#d62728", read_dqn),
    ):
        try:
            steps, pipes = reader(path)
        except FileNotFoundError:
            print(f"skipping {path}, not found")
            continue
        if not steps:
            continue
        axes.plot(steps, smooth(pipes, args.smooth), color=colour, label=label, lw=1.8)
        axes.plot(steps, pipes, color=colour, alpha=0.15, lw=0.8)

    axes.axhline(args.target, color="#666666", ls="--", lw=1,
                 label=f"target, {args.target:g} pipes")
    axes.set_xlabel("environment steps")
    axes.set_ylabel("pipes cleared per episode")
    axes.set_title("Flappy Bird from raw pixels")
    axes.legend(frameon=False)
    axes.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    figure.savefig(args.out, dpi=140)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
