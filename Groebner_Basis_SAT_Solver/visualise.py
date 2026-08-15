"""Draw the three things this solver's README argues in prose.

    python visualise.py

Writes `algebra_encoding.png`, `phase_transition.png` and
`elimination_contribution.png` next to this file. Everything is computed with
the modules in this folder; nothing is stated here that the code does not do.
"""

import time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from polynomial import UnsatError  # noqa: E402
from utils import generate_3sat, sat_to_polynomials  # noqa: E402
from solver import polynomial_Solver, triangular_Grobner_Basis  # noqa: E402
from linear_algebra import monomial_basis, system_to_matrix, dedup_rows, gauss_elim_gf2  # noqa: E402

plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 120})

INSTANCES = 60
PHASE_TRANSITION = 4.26      # the random 3-SAT threshold
BENCHMARK_RATIO = 3.0        # what this repository's own tests use


def draw_algebra_encoding(num_vars=8, num_clauses=16, seed=7):
    """Clauses to polynomials to a GF(2) matrix, before and after elimination.

    Every clause becomes one polynomial whose zeros are exactly its satisfying
    assignments. Treating each distinct monomial as an unknown turns the whole
    system into a matrix over GF(2), and row reduction pushes it into echelon
    form. The triangular shape in the right-hand panel is the whole idea of the
    method, drawn.
    """
    clauses = generate_3sat(num_vars, num_clauses, seed=seed)
    polys = sat_to_polynomials(clauses, num_vars)
    basis = monomial_basis(polys)
    rows = dedup_rows(system_to_matrix(polys, basis))
    reduced = gauss_elim_gf2(rows)

    before, after = np.array(rows), np.array(reduced)
    figure, (left, right) = plt.subplots(1, 2, figsize=(12, 4.6))
    for axes, data, title in (
        (left, before, f"encoded: {before.shape[0]} equations over {before.shape[1]} monomials"),
        (right, after, "after row reduction over GF(2)"),
    ):
        axes.imshow(data, cmap="Greys", interpolation="nearest", aspect="auto")
        axes.set_title(title, fontsize=11)
        axes.set_xlabel("monomial (constant first, then by degree)")
        axes.set_ylabel("equation")

    # Trace the pivots. The staircase they make is the triangular form itself.
    pivots = [(r, next((c for c, v in enumerate(row) if v), None))
              for r, row in enumerate(after)]
    pivots = [(r, c) for r, c in pivots if c is not None]
    right.step([c for _, c in pivots], [r for r, _ in pivots], where="post",
               color="#d62728", lw=2, label="leading term of each equation")
    right.legend(frameon=False, fontsize=9, loc="lower left")

    figure.suptitle(
        f"A {num_vars}-variable, {num_clauses}-clause 3-SAT instance as a GF(2) linear system",
        fontsize=13)
    figure.tight_layout()
    figure.savefig("algebra_encoding.png", bbox_inches="tight")
    print(f"algebra_encoding.png: {before.shape[0]}x{before.shape[1]} matrix, "
          f"{len(pivots)} pivots, density {before.mean():.2f} before, {after.mean():.2f} after")


def _elimination_alone_says_unsat(polys):
    """Does the triangular elimination, with no branching, derive 1 = 0?"""
    try:
        triangular_Grobner_Basis(list(polys), {})
        return False
    except UnsatError:
        return True


def measure(num_vars, ratios, instances, seed0=1000):
    """For each clause-to-variable ratio: how many are satisfiable, and how many
    the elimination step resolves on its own."""
    satisfiable, unsat_counts, caught_counts, seed = [], [], [], seed0
    for ratio in ratios:
        num_clauses = max(1, round(ratio * num_vars))
        sat_count, caught_count, unsat_count = 0, 0, 0
        for _ in range(instances):
            seed += 1
            clauses = generate_3sat(num_vars, num_clauses, seed=seed)
            polys = sat_to_polynomials(clauses, num_vars)
            is_sat = polynomial_Solver(list(polys), num_vars) is not None
            sat_count += is_sat
            if not is_sat:
                unsat_count += 1
                caught_count += _elimination_alone_says_unsat(polys)
        satisfiable.append(sat_count / instances)
        unsat_counts.append(unsat_count)
        caught_counts.append(caught_count)
        print(f"  m/n={ratio:>4.1f}  satisfiable {satisfiable[-1]:>5.0%}   "
              f"unsatisfiable {unsat_count:>3}   elimination caught {caught_count}")
    return np.array(satisfiable), np.array(unsat_counts), np.array(caught_counts)


def draw_phase_transition(ratios, satisfiable, num_vars, instances):
    figure, axes = plt.subplots(figsize=(8, 4.6))
    axes.plot(ratios, satisfiable * 100, marker="o", color="#1f77b4")
    axes.axvline(PHASE_TRANSITION, ls="--", c="#d62728", lw=1.3,
                 label=f"phase transition, m/n = {PHASE_TRANSITION}")
    axes.axvline(BENCHMARK_RATIO, ls=":", c="#555555", lw=1.6,
                 label=f"where this repo benchmarks, m/n = {BENCHMARK_RATIO:g}")
    axes.set_xlabel("clauses per variable, m/n")
    axes.set_ylabel("satisfiable instances (%)")
    axes.set_title(f"Where the hard instances are, n={num_vars}, {instances} per ratio")
    axes.legend(frameon=False)
    figure.tight_layout()
    figure.savefig("phase_transition.png", bbox_inches="tight")
    print("phase_transition.png written")


def draw_elimination_contribution(ratios, unsat_counts, caught_counts, num_vars):
    """Counts, not percentages: a chart of zeroes says nothing, but a chart of
    what there was to catch next to what was caught says exactly the thing."""
    figure, axes = plt.subplots(figsize=(8.5, 4.6))
    axes.bar(ratios - 0.06, unsat_counts, width=0.12, color="#c0c4c8",
             label="unsatisfiable instances")
    axes.bar(ratios + 0.06, caught_counts, width=0.12, color="#2ca02c",
             label="caught by the elimination alone")
    axes.axvline(PHASE_TRANSITION, ls="--", c="#d62728", lw=1.3,
                 label=f"phase transition, m/n = {PHASE_TRANSITION}")
    total_unsat, total_caught = int(unsat_counts.sum()), int(caught_counts.sum())
    axes.annotate(f"{total_caught} of {total_unsat} caught",
                  xy=(0.5, 0.72), xycoords="axes fraction", ha="center",
                  fontsize=15, color="#2ca02c", fontweight="bold")
    axes.set_xlabel("clauses per variable, m/n")
    axes.set_ylabel(f"instances out of {INSTANCES} per ratio")
    axes.set_title(f"The elimination step is nearly inert, n={num_vars}. "
                   "The branching does the work.", fontsize=12)
    axes.legend(frameon=False, loc="upper left")
    figure.tight_layout()
    figure.savefig("elimination_contribution.png", bbox_inches="tight")
    print(f"elimination_contribution.png: {total_caught} of {total_unsat} caught")


if __name__ == "__main__":
    started = time.time()
    draw_algebra_encoding()

    NUM_VARS = 12
    ratios = np.arange(2.0, 7.01, 0.5)
    print(f"\nmeasuring n={NUM_VARS}, {INSTANCES} instances per ratio:")
    satisfiable, unsat_counts, caught_counts = measure(NUM_VARS, ratios, INSTANCES)

    draw_phase_transition(ratios, satisfiable, NUM_VARS, INSTANCES)
    draw_elimination_contribution(ratios, unsat_counts, caught_counts, NUM_VARS)
    print(f"\ndone in {time.time() - started:.0f}s")
