from pysat.formula import CNF
from pysat.solvers import Minisat22


def brute_decide(clauses):
    """Reference SAT‐decision: True if satisfiable, else False."""
    f = CNF()
    for cl in clauses:
        f.append(cl)
    with Minisat22(bootstrap_with=f) as solver:
        return solver.solve()


def test_solve_triangular(num_tests=100000, num_vars=20, num_clauses=60, seed=None):
    """
    Stress‐test `solve_with_random` against MiniSat.
    Generates random 3-CNF instances and checks decision result.
    Stops on first mismatch.
    """
    if seed is not None:
        random.seed(seed)

    for t in range(1, num_tests+1):
        # 1) generate a random 3-SAT instance
        clauses = generate_3sat(num_vars, num_clauses)

        polys = sat_to_polynomials(clauses, num_vars)
        try:
            basis,var_assign=triangular_Grobner_Basis(polys,{})
        except UnsatError:
            my_sat = False
        else:
            my_sat = True

        # 3) decide with reference solver
        ref_sat = brute_decide(clauses)

        # 4) compare
        if my_sat != ref_sat:
            print(f"\n❌ MISMATCH on test #{t}")
            print(" Clauses:", clauses)
            print(" triangular_Grobner_Basis says:", "SAT" if my_sat else "UNSAT")
            print(" Solution:", var_assign)
            print(" Reference says     :", "SAT" if ref_sat else "UNSAT")
            return

        if t % 1000 == 0:
            print(f"✓ {t} tests passed")

    print(f"\n✅ All {num_tests} tests passed without disagreement.")


if __name__ == "__main__":
    # adjust parameters as needed
    test_solve_triangular(
        num_tests=100000,
        num_vars=20,
        num_clauses=60,
        seed=12345
    )
