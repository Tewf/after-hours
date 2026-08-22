"""The two-phase simplex, in exact rationals, under Bland's rule.

One role: answer a linear programme over the rationals. Integrality is
[`branch_and_bound.py`](branch_and_bound.py)'s problem, and it is the only caller
that matters here.

Everything is a `Fraction`. Nothing is ever a float, so there is no pivot
tolerance to tune and no basis that is only degenerate to fifteen digits. That
costs speed and buys the one property this is for: an answer that is a fact about
the programme rather than about the arithmetic.

**Phase I and phase II are two explicit phases**, after Dantzig. Phase I gives
every row that cannot start from a slack an artificial variable and minimises
their sum; a positive minimum is a proof of infeasibility, and the artificials
are then driven out and their columns dropped. Phase II runs the real objective
from the basis phase I left.

**Bland's smallest-subscript rule decides every pivot**, entering and leaving.
It is the slowest of the standard rules and the only one that cannot cycle, and
a solver that hangs on a degenerate vertex is worse here than a slow one.
"""

from fractions import Fraction

MAXIMISE, MINIMISE = "max", "min"
OPTIMAL, INFEASIBLE, UNBOUNDED = "optimal", "infeasible", "unbounded"


class Programme:
    """`sense` of `objective . x`, subject to `rows`, with every `x >= 0`.

    A row is `(coefficients, relation, rhs)` and a relation is one of `<=`, `>=`
    or `=`. Bounds added by branching arrive as ordinary rows, which is why no
    variable here carries one of its own.
    """

    def __init__(self, objective, rows, sense=MAXIMISE, integral=()):
        self.objective = [Fraction(value) for value in objective]
        self.rows = [([Fraction(value) for value in coefficients], relation, Fraction(rhs))
                     for coefficients, relation, rhs in rows]
        self.sense = sense
        self.integral = tuple(sorted(integral))

    @property
    def width(self):
        return len(self.objective)

    def value_at(self, point):
        return sum((c * x for c, x in zip(self.objective, point)), Fraction(0))

    def with_row(self, coefficients, relation, rhs):
        """The same programme, one constraint tighter. Branching's only move."""
        return Programme(self.objective, self.rows + [(coefficients, relation, rhs)],
                         self.sense, self.integral)

    def satisfies(self, point):
        for coefficients, relation, rhs in self.rows:
            total = sum((c * x for c, x in zip(coefficients, point)), Fraction(0))
            if relation == "<=" and total > rhs: return False
            if relation == ">=" and total < rhs: return False
            if relation == "=" and total != rhs: return False
        return all(x >= 0 for x in point)


def _equality_form(programme):
    """(tableau rows, basis, count of artificials) with every row an equality.

    A row with a negative right-hand side is negated first, relation and all,
    because phase I starts from a basis of slacks and artificials and that basis
    is only feasible where every right-hand side is non-negative.
    """
    rows, relations = [], []
    for coefficients, relation, rhs in programme.rows:
        if rhs < 0:
            coefficients = [-c for c in coefficients]
            rhs = -rhs
            relation = {"<=": ">=", ">=": "<=", "=": "="}[relation]
        rows.append((list(coefficients), rhs))
        relations.append(relation)

    slack_count = sum(1 for relation in relations if relation != "=")
    artificial_count = sum(1 for relation in relations if relation != "<=")
    width = programme.width + slack_count + artificial_count

    tableau, basis, slack_at, artificial_at = [], [], programme.width, programme.width + slack_count
    for (coefficients, rhs), relation in zip(rows, relations):
        line = coefficients + [Fraction(0)] * (width - programme.width) + [rhs]
        if relation == "<=":
            line[slack_at] = Fraction(1)
            basis.append(slack_at)
            slack_at += 1
        elif relation == ">=":
            line[slack_at] = Fraction(-1)
            line[artificial_at] = Fraction(1)
            basis.append(artificial_at)
            slack_at += 1
            artificial_at += 1
        else:
            line[artificial_at] = Fraction(1)
            basis.append(artificial_at)
            artificial_at += 1
        tableau.append(line)
    return tableau, basis, artificial_count


def _pivot(tableau, basis, row, column):
    factor = tableau[row][column]
    tableau[row] = [value / factor for value in tableau[row]]
    for index, line in enumerate(tableau):
        if index != row and line[column] != 0:
            scale = line[column]
            tableau[index] = [value - scale * other for value, other in zip(line, tableau[row])]
    basis[row] = column


def _minimise(tableau, basis, cost, columns):
    """Drive `cost` down to its minimum over `columns`; True unless unbounded.

    The reduced costs are recomputed from the basis each round rather than
    carried in an objective row, which is slower and keeps one fewer thing that
    can drift out of step with the tableau it describes.
    """
    while True:
        price = [cost[column] for column in range(columns)]
        for row, basic in enumerate(basis):
            if cost[basic] != 0:
                price = [value - cost[basic] * tableau[row][column]
                         for column, value in enumerate(price)]
        entering = next((column for column in range(columns)
                         if price[column] < 0 and column not in basis), None)
        if entering is None:
            return True

        ratios = [(line[-1] / line[entering], basis[row], row)
                  for row, line in enumerate(tableau) if line[entering] > 0]
        if not ratios:
            return False
        _pivot(tableau, basis, min(ratios)[2], entering)


def solve(programme):
    """(status, point, value). The point is exact and is checked before it is returned."""
    tableau, basis, artificials = _equality_form(programme)
    columns = len(tableau[0]) - 1 if tableau else programme.width
    real = columns - artificials

    if artificials:
        cost = [Fraction(0)] * real + [Fraction(1)] * artificials
        _minimise(tableau, basis, cost, columns)
        if any(basis[row] >= real and tableau[row][-1] != 0 for row in range(len(tableau))):
            return INFEASIBLE, None, None
        # An artificial left in the basis at zero is a redundant row, not an
        # infeasibility. Pivot it out onto any real column that can take it; a
        # row where none can is `0 = 0`, a constraint the others already imply,
        # and it is dropped. Leaving it in is what put an artificial's index in
        # front of phase II's objective, which has one entry per real column.
        #
        # Dropping is safe in this order: such a row is zero across every real
        # column, so a pivot on a real column never touches it, and a row that
        # cannot be pivoted out now could not have been earlier either.
        keep = []
        for row, basic in enumerate(basis):
            swap = None
            if basic >= real:
                swap = next((column for column in range(real) if tableau[row][column] != 0), None)
                if swap is None:
                    continue
                _pivot(tableau, basis, row, swap)
            keep.append(row)
        tableau = [tableau[row][:real] + [tableau[row][-1]] for row in keep]
        basis = [basis[row] for row in keep]
        columns = real

    sign = -1 if programme.sense == MAXIMISE else 1
    cost = [sign * value for value in programme.objective] + [Fraction(0)] * (columns - programme.width)
    if not _minimise(tableau, basis, cost, columns):
        return UNBOUNDED, None, None

    point = [Fraction(0)] * programme.width
    for row, basic in enumerate(basis):
        if basic < programme.width:
            point[basic] = tableau[row][-1]
    if not programme.satisfies(point):
        raise ArithmeticError("the simplex returned a point outside the programme: %s" % (point,))
    return OPTIMAL, point, programme.value_at(point)
