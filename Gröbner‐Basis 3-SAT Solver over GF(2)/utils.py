import random
# ---------- 3-SAT → Polynomials ----------
def sat_to_polynomials(clauses, num_vars):
    zero = (0,) * num_vars
    polys = []
    for clause in clauses:
        f = Polynomial({zero: 1}, num_vars)
        for lit in clause:
            idx = abs(lit) - 1
            m = [0] * num_vars; m[idx] = 1
            factor = (Polynomial({zero: 1, tuple(m): 1}, num_vars)
                      if lit > 0 else Polynomial({tuple(m): 1}, num_vars))
            prod = {}
            for m1, c1 in f.terms.items():
                for m2, c2 in factor.terms.items():
                    mm = tuple(1 if (a or b) else 0 for a, b in zip(m1, m2))
                    cc = (c1 * c2) & 1
                    prod[mm] = (prod.get(mm, 0) + cc) & 1
                    if prod[mm] == 0:
                        del prod[mm]
            f = Polynomial(prod, num_vars)
        polys.append(f)
    return polys
# ---------- Verifier & Generator ----------
def verify_solution(clauses, assign):
    for cl in clauses:
        if not any((lit>0 and assign.get(abs(lit)-1,0)==1) or
                   (lit<0 and assign.get(abs(lit)-1,0)==0)
                   for lit in cl):
            return False
    return True

def generate_3sat(num_vars, num_clauses, seed=None):
    if seed is not None:
        random.seed(seed)
    out = []
    for _ in range(num_clauses):
        vs = random.sample(range(num_vars),3)
        out.append([random.choice([1,-1])*(i+1) for i in vs])
    return out
