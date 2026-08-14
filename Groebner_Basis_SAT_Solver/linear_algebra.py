"""Gaussian elimination over GF(2) on the monomial-linearised system.

The triangular elimination in solver.py only spots a contradiction when a
*single* polynomial collapses to the constant 1. It cannot see a contradiction
that only appears once several equations are XORed together.

This module recovers that. Treat every distinct monomial in the system as an
independent unknown, which turns the polynomial system into a linear system
over GF(2); row-reduce it; and look for a row asserting 1 = 0.

Linearisation is a relaxation -- it forgets that x*y is determined by x and y --
so every solution of the polynomial system is still a solution of the linear
one. That makes the test **sound but incomplete**: a contradiction found here is
real, but plenty of unsatisfiable systems slip through.

Adapted from the Gaussian-elimination-mod-2 routine in the earlier
`3sat_to_polynomial_system` notebook, which worked on sympy expressions; here it
works directly on the Polynomial class.
"""


def monomial_basis(polys):
    """Every distinct monomial in the system, as an ordered list.

    The constant monomial is forced to index 0 so the contradiction check has a
    fixed column to look at.
    """
    seen = set()
    num_vars = polys[0].num_vars if polys else 0
    constant = (0,) * num_vars
    for p in polys:
        seen.update(p.terms)
    seen.discard(constant)
    return [constant] + sorted(seen, key=lambda m: (sum(m), m))


def system_to_matrix(polys, basis):
    """One row per polynomial: 1 where that monomial is present."""
    index = {m: i for i, m in enumerate(basis)}
    rows = []
    for p in polys:
        row = [0] * len(basis)
        for mono, coef in p.terms.items():
            if coef & 1:
                row[index[mono]] = 1
        rows.append(row)
    return rows


def dedup_rows(rows):
    """Drop all-zero rows and duplicates -- they carry no information."""
    out, seen = [], set()
    for row in rows:
        key = tuple(row)
        if any(row) and key not in seen:
            seen.add(key)
            out.append(row)
    return out


def gauss_elim_gf2(rows):
    """Row-echelon form over GF(2). Returns a new list; the input is untouched."""
    m = [list(r) for r in rows]
    if not m:
        return m
    num_rows, num_cols = len(m), len(m[0])
    r = 0
    for c in range(num_cols):
        if r >= num_rows:
            break
        pivot = next((i for i in range(r, num_rows) if m[i][c]), None)
        if pivot is None:
            continue
        m[r], m[pivot] = m[pivot], m[r]
        for i in range(r + 1, num_rows):
            if m[i][c]:
                m[i] = [a ^ b for a, b in zip(m[i], m[r])]
        r += 1
    return m


def detects_contradiction(polys):
    """True if XORing equations derives 1 = 0. Sound; never a false positive."""
    polys = [p for p in polys if not p.is_zero()]
    if not polys:
        return False
    basis = monomial_basis(polys)
    reduced = gauss_elim_gf2(dedup_rows(system_to_matrix(polys, basis)))
    # column 0 is the constant term: a row that is 1 there and 0 everywhere
    # else reads "1 = 0".
    return any(row[0] == 1 and not any(row[1:]) for row in reduced)
