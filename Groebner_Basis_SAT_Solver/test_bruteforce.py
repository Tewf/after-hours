"""Verification against exhaustive enumeration -- no PySAT required.

tests.py cross-checks against MiniSat, which means it only runs where PySAT is
installed. This file needs nothing but the standard library, and checks more:
for a SAT verdict it validates the returned *assignment*, not just the verdict.

Run: python test_bruteforce.py
"""

import itertools
import random

from linear_algebra import detects_contradiction
from solver import triangular_Grobner_Basis, polynomial_Solver, UnsatError
from utils import generate_3sat, sat_to_polynomials, verify_solution


def brute_force(clauses, num_vars):
    """Ground truth: a satisfying assignment, or None. O(2^n) -- small n only."""
    for bits in itertools.product((0, 1), repeat=num_vars):
        assign = {i: b for i, b in enumerate(bits)}
        if verify_solution(clauses, assign):
            return assign
    return None


def test_worked_example():
    """The example worked by hand in the original write-up.

        (x ∨ x ∨ y) ∧ (¬x ∨ ¬y ∨ ¬y) ∧ (¬x ∨ y ∨ y)   ⇒   x = 0, y = 1

    The only deterministic fixture here; everything else is random instances.
    """
    clauses = [[1, 1, 2], [-1, -2, -2], [-1, 2, 2]]
    assert verify_solution(clauses, {0: 0, 1: 1}), "the expected answer must satisfy"
    sol = polynomial_Solver(sat_to_polynomials(clauses, 2), 2)
    assert sol is not None, "solver called a satisfiable instance UNSAT"
    assert verify_solution(clauses, sol), f"solver returned a non-solution: {sol}"
    print("✓ worked example solved:", sol)


def test_trivially_unsat():
    """All 8 clauses over 3 variables -- no assignment can satisfy every one."""
    clauses = [[a, b, c] for a in (1, -1) for b in (2, -2) for c in (3, -3)]
    assert brute_force(clauses, 3) is None, "fixture must really be UNSAT"
    assert polynomial_Solver(sat_to_polynomials(clauses, 3), 3) is None
    print("✓ trivially unsatisfiable instance rejected")


def test_against_brute_force(num_tests=150, num_vars=10, num_clauses=45, seed=0):
    """Random instances, checked against exhaustive search."""
    random.seed(seed)
    unsound_elim = 0
    for t in range(1, num_tests + 1):
        clauses = generate_3sat(num_vars, num_clauses)
        really_sat = brute_force(clauses, num_vars) is not None

        sol = polynomial_Solver(sat_to_polynomials(clauses, num_vars), num_vars)
        assert (sol is not None) == really_sat, (
            f"instance #{t}: solver said {'SAT' if sol else 'UNSAT'}, "
            f"truth is {'SAT' if really_sat else 'UNSAT'}: {clauses}")
        if sol is not None:
            assert verify_solution(clauses, sol), (
                f"instance #{t}: returned assignment does not satisfy: {sol}")

        # the pruning tests must never claim a contradiction on a SAT instance
        if really_sat:
            polys = sat_to_polynomials(clauses, num_vars)
            if detects_contradiction(polys):
                unsound_elim += 1
            try:
                triangular_Grobner_Basis(polys, {})
            except UnsatError:
                unsound_elim += 1
    assert unsound_elim == 0, f"{unsound_elim} unsound UNSAT claims on SAT instances"
    print(f"✓ {num_tests} random instances at n={num_vars}, m={num_clauses} "
          f"match exhaustive search")


if __name__ == "__main__":
    test_worked_example()
    test_trivially_unsat()
    # 500 instances in total, which is the number this repository claims.
    test_against_brute_force(200, 8, 30, seed=1)
    test_against_brute_force(200, 10, 45, seed=2)
    test_against_brute_force(100, 12, 51, seed=3)
    print("\nAll checks passed.")
