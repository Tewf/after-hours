"""Gauss-Jordan inversion in exact integer arithmetic, no floating point anywhere.

The idea is to never divide during elimination. To clear entry (j, i) against a
pivot p, scale row j by p/g and row i by the entry/g, where g is their gcd, and
subtract. Both multipliers are integers, so the matrix stays integral and the
result is exact rather than nearly right.

Three things the earlier version got wrong, all of which defeated the one
property it existed to demonstrate:

- **No pivoting.** A zero pivot made both multipliers zero, which annihilated
  the row instead of failing. On [[0,1,1],[1,0,1],[1,1,0]], which is invertible,
  it returned an all-zero matrix and a divide-by-zero warning.
- **int64.** Entries grow multiplicatively with no reduction, so exactness
  silently ended around n=8 where the true values need 26 digits. Python
  integers are unbounded; the arrays here hold objects, not machine words.
- **It stopped one step short.** It produced [D | D*A^-1] and never divided, so
  it never actually returned an inverse.

Row contents are reduced by their gcd after each elimination, which keeps the
integers from growing without bound and does not disturb the result: scaling a
row of [D | D*A^-1] scales that row of D by the same factor.
"""

from fractions import Fraction
from math import gcd

import numpy as np


def elimination_multipliers(entry, pivot):
    """Integer pair (for the target row, for the pivot row) that clears `entry`.

    Not a least common multiple, which is what this was previously named. It is
    the pair of cofactors whose difference cancels: entry*(pivot/g) - pivot*(entry/g).
    """
    divisor = gcd(int(entry), int(pivot))
    if divisor == 0:
        return 0, 0
    return pivot // divisor, entry // divisor


def _reduce_row(row):
    """Divide a row through by the gcd of its entries, to bound growth."""
    divisor = 0
    for value in row:
        divisor = gcd(divisor, int(value))
    if divisor > 1:
        for k in range(len(row)):
            row[k] //= divisor
    return row


def diagonalise(matrix):
    """Reduce [A | I] to [D | D @ A^-1] with D diagonal, exactly.

    Raises ValueError if A is singular.
    """
    matrix = np.array(matrix, dtype=object)
    n = matrix.shape[0]
    if matrix.shape[1] != n:
        raise ValueError(f"expected a square matrix, got shape {matrix.shape}")

    identity = np.array([[int(r == c) for c in range(n)] for r in range(n)], dtype=object)
    augmented = np.hstack((matrix, identity))

    for i in range(n):
        if augmented[i, i] == 0:
            candidates = [r for r in range(i + 1, n) if augmented[r, i] != 0]
            if not candidates:
                raise ValueError(f"matrix is singular: column {i} has no usable pivot")
            augmented[[i, candidates[0]]] = augmented[[candidates[0], i]]

        pivot = augmented[i, i]
        for j in range(n):
            if j == i or augmented[j, i] == 0:
                continue
            scale_j, scale_i = elimination_multipliers(augmented[j, i], pivot)
            augmented[j, :] = scale_j * augmented[j, :] - scale_i * augmented[i, :]
            _reduce_row(augmented[j, :])

    return augmented


def inverse(matrix):
    """Exact inverse as an array of `Fraction`, with no floating point involved."""
    n = np.asarray(matrix).shape[0]
    augmented = diagonalise(matrix)
    result = np.empty((n, n), dtype=object)
    for i in range(n):
        diagonal = augmented[i, i]
        for j in range(n):
            result[i, j] = Fraction(int(augmented[i, n + j]), int(diagonal))
    return result


def to_float(matrix):
    """Fractions to floats, for comparing against `numpy.linalg.inv`."""
    return np.array([[float(value) for value in row] for row in matrix], dtype=float)
