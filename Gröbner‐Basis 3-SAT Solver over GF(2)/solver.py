def local_test(poly, var_assign):
    """
    Try to force exactly one variable in `poly` under the current var_assign.
    - If poly ≡ 1, raises UnsatError.
    - If setting x_v=1 ⇒ 1=0, force x_v=0 and return the reduced polynomial with x_v substituted.
    - Else if x_v=0 ⇒ 1=0, force x_v=1 and return the reduced polynomial.
    - Otherwise return None to signal “no single-variable force.”
    """
    if poly.is_constant_one():
        # 1 = 0 ⇒ contradiction
        raise UnsatError

    # collect any variable that actually appears
    vars_in_poly = list({i for m in poly.terms for i,e in enumerate(m) if e})
    if not vars_in_poly:
        # no variables left ⇒ nothing to force
        return None

    v = random.choice(vars_in_poly)

    # try x_v = 1
    p1 = poly.substitute_var(v, 1)
    if p1.is_constant_one():
        # that would force 1 = 0, so we know x_v must be 0
        var_assign[v] = 0
        # return the clause with x_v = 0 substituted away
        return poly.substitute_var(v, 0)

    # try x_v = 0
    p0 = poly.substitute_var(v, 0)
    if p0.is_constant_one():
        var_assign[v] = 1
        return poly.substitute_var(v, 1)

    # no single‐step forced assignment
    return None


def triangular_Grobner_Basis(polys, var_assign):
    """
    Recursively compute a triangular Gröbner basis for `polys` over GF(2)
    under the current partial assignment `var_assign`.  Returns

        basis_list, var_assign

    where `basis_list` is a list of Polynomials [g1, g2, …] each of the form
    lead_monomial + rest = 0, in triangular (lex) order.  Raises UnsatError
    immediately if 1=0 is derived anywhere.
    """
    # 1) Unit‑propagate on every polynomial
    simplified = []
    for p in polys:
        # keep forcing bits until stable
        while True:
            forced = local_test(p, var_assign)
            if forced is None:
                break
            # we got back a new polynomial with one bit substituted; re‑apply subs
            p = forced.substitute(var_assign)
        # finally apply all bits
        p = p.substitute(var_assign)
        if p.is_constant_one():
            # immediate contradiction
            raise UnsatError
        if not p.is_zero():
            simplified.append(p)
    polys = simplified

    # 2) Base case: no equations left → SAT, empty basis
    if not polys:
        return [], var_assign

    # 3) Pick pivot: the polynomial with maximal (degree, lead_monomial)
    pivot_idx = max(range(len(polys)),
                    key=lambda j: (polys[j].degree(), polys[j].lead_monomial()))
    pivot = polys.pop(pivot_idx)

    # 4) Split pivot = M + L
    M = pivot.lead_monomial()
    L_terms = {m: c for m,c in pivot.terms.items() if m != M}
    L_poly  = Polynomial(L_terms, pivot.num_vars)

    # 5) Eliminate M from the rest
    for i in range(len(polys)):
        polys[i] = polys[i].inject_monomial(M, L_poly, var_assign)

    # 6) Recurse on the smaller system
    basis_tail, var_assign = triangular_Grobner_Basis(polys, var_assign)

    # 7) Our triangular basis is [pivot] + tail
    return [pivot] + basis_tail, var_assign
