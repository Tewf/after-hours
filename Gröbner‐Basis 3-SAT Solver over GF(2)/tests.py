# tests.py

import random
from pysat.formula import CNF
from pysat.solvers import Minisat22

from utils import generate_3sat, sat_to_polynomials
from solver import triangular_Grobner_Basis, polynomial_Solver, UnsatError

def brute_decide(clauses):
    """Reference SAT‐decision: True if satisfiable, else False."""
    f = CNF()
    for cl in clauses:
        f.append(cl)
    with Minisat22(bootstrap_with=f) as solver:
        return solver.solve()

def test_solve_triangular(num_tests=10000, num_vars=20, num_clauses=60, seed=None):
    """
    Stress‐test `triangular_Grobner_Basis` as a SAT‐decision oracle.
    Generates random 3-CNF instances and checks decision result.
    Stops on first mismatch.
    """
    if seed is not None:
        random.seed(seed)

    for t in range(1, num_tests + 1):
        clauses = generate_3sat(num_vars, num_clauses)
        polys   = sat_to_polynomials(clauses, num_vars)

        # 1) decide by triangular elimination alone
        try:
            basis, var_assign = triangular_Grobner_Basis(polys, {})
            my_sat = True
        except UnsatError:
            my_sat = False

        # 2) reference solver
        ref_sat = brute_decide(clauses)

        if my_sat != ref_sat:
            print(f"\n❌ MISMATCH on test #{t}")
            print(" Clauses:       ", clauses)
            print(" triangular says:", "SAT" if my_sat else "UNSAT")
            print(" Solution:      ", var_assign if my_sat else None)
            print(" Reference says:", "SAT" if ref_sat else "UNSAT")
            return

        if t % 1000 == 0:
            print(f"✓ triangular: {t} tests passed")

    print(f"\n✅ triangular_Grobner_Basis passed all {num_tests} tests.")

def test_full_solver(num_tests=10000, num_vars=20, num_clauses=60, seed=None):
    """
    Stress‐test `polynomial_Solver` (with branching) against MiniSat.
    """
    if seed is not None:
        random.seed(seed)

    for t in range(1, num_tests + 1):
        clauses = generate_3sat(num_vars, num_clauses)
        polys   = sat_to_polynomials(clauses, num_vars)

        # 1) decide by full recursive solver
        sol = polynomial_Solver(polys, num_vars)
        my_sat = sol is not None

        # 2) reference solver
        ref_sat = brute_decide(clauses)

        if my_sat != ref_sat:
            print(f"\n❌ MISMATCH on test #{t}")
            print(" Clauses:        ", clauses)
            print(" polynomial_Solver says:", "SAT" if my_sat else "UNSAT")
            print(" Solution:       ", sol)
            print(" Reference says: ", "SAT" if ref_sat else "UNSAT")
            return

        if t % 1000 == 0:
            print(f"✓ full solver: {t} tests passed")

    print(f"\n✅ polynomial_Solver passed all {num_tests} tests.")

if __name__ == "__main__":
    random.seed(12345)
    print("Running triangular elimination tests...")
    test_solve_triangular(num_tests=20000, num_vars=20, num_clauses=60)
    print("\nRunning full solver tests...")
    test_full_solver   (num_tests=20000, num_vars=20, num_clauses=60)
