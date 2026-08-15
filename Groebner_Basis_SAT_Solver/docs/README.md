# Earlier write-up (October 2023): superseded

`Solving_boolean_formulas_in_GF2.pdf` is my first attempt at this problem,
written a year and a half before the solver in this directory. It is kept for
the record, and because the reduction it sets out is the one still used here:
every propositional formula maps into Z₂ via `¬x = x ⊕ 1` and
`x ∨ y = x ⊕ y ⊕ xy`, giving a polynomial system whose solutions are exactly
the satisfying assignments.

**Its central claim is wrong, and knowingly kept here as a record of that.**
The paper argues that the resulting system can be solved in polynomial time,
and therefore, though it does not say so, that P = NP. The argument fails in
its own §4, "Cas 2":

> « Par précaution, on choisira 0 quand on ne peut plus simplifier un système. »

That is an unbacktracked guess. Repairing it requires branching on the guess,
which is exactly the step that makes the procedure exponential, and is what
`polynomial_Solver` in this directory actually does. A second gap: §5 bounds
the monomial count by that of the *initial* 3-CNF system, O(n³), but
substitution raises the degree of every term the substituted monomial divides,
so the bound does not survive iteration.

The working solver is honest about this: `triangular_Grobner_Basis` is
polynomial, `polynomial_Solver` is worst-case exponential, and 3-SAT stays
NP-complete.
