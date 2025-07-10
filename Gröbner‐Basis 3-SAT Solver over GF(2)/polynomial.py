# ---------- Exceptions ----------
class UnsatError(Exception):
    """Raised when a direct contradiction (1=0) is detected."""
    pass

# ---------- Utility ----------
def monomial_divides(M, mono):
    return all(mi <= ui for mi, ui in zip(M, mono))

# ---------- Polynomial over GF(2) ----------
class Polynomial:
    def __init__(self, terms=None, num_vars=0):
        self.num_vars = num_vars
        self.terms = {}
        if terms:
            for mono, coef in terms.items():
                m = tuple(1 if e else 0 for e in mono)
                c = coef & 1
                if c:
                    self.terms[m] = (self.terms.get(m, 0) + 1) & 1
                    if self.terms[m] == 0:
                        del self.terms[m]
    def __repr__(self):
        return f"Poly({self.terms})"
    def is_zero(self):
        return not self.terms
    def is_constant_one(self):
        return self.terms == {(0,) * self.num_vars: 1}
    def degree(self):
        return max((sum(m) for m in self.terms), default=0)
    def lead_monomial(self):
        return max(self.terms, key=lambda m: (sum(m), m)) if self.terms else None
    def substitute_var(self, v, val):
        new_terms = {}
        for mono, coef in self.terms.items():
            if val == 0 and mono[v] == 1:
                continue
            m2 = list(mono)
            if val == 1:
                m2[v] = 0
            m2 = tuple(m2)
            new_terms[m2] = (new_terms.get(m2, 0) + coef) & 1
            if new_terms[m2] == 0:
                del new_terms[m2]
        return Polynomial(new_terms, self.num_vars)
    def substitute(self, var_assign):
        p = self
        for v, val in var_assign.items():
            p = p.substitute_var(v, val)
        return p
    def inject_monomial(self, M, L, var_assign):
        """
        Replace every occurrence of M in `self` by L, carrying along any extra factors:
            for each term mono = M * rest in self:
                replace coef*mono  with  coef*(L * rest).
        """
        # 1) first apply current variable assignments to L
        Lsub = L.substitute(var_assign)

        new_terms = {}
        for mono, coef in self.terms.items():
            if monomial_divides(M, mono):
                # decompose mono = M * rest
                rest = tuple(ui - mi for ui, mi in zip(mono, M))
                # now distribute L across rest:
                #   each (lt, c) in Lsub contributes c*(lt * rest)
                for lt, c in Lsub.terms.items():
                    # multiply lt·rest in GF(2) by bitwise-OR of exponent tuples
                    new_m = tuple(1 if (r or l) else 0
                                for r, l in zip(rest, lt))
                    v = (coef * c) & 1
                    if v:
                        new_terms[new_m] = (new_terms.get(new_m, 0) + v) & 1
                        if new_terms[new_m] == 0:
                            del new_terms[new_m]
            else:
                # leave untouched terms alone
                v = coef & 1
                if v:
                    new_terms[mono] = (new_terms.get(mono, 0) + v) & 1
                    if new_terms[mono] == 0:
                        del new_terms[mono]

        return Polynomial(new_terms, self.num_vars)
