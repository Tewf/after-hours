"""Trace of a matrix product, without forming the product.

tr(XY) needs only the diagonal of XY, so computing all n^2 entries to sum n of
them is wasteful. Splitting both matrices into quadrants gives

    tr(XY) = tr(X0 Y0) + tr(X1 Y2) + tr(X2 Y1) + tr(X3 Y3)

and recursing bottoms out at scalars. The result is O(n^2) rather than the
O(n^3) of multiplying first.

Worth saying plainly: `numpy.sum(x * y.T)` is the same O(n^2) in one line and is
faster than this in practice. The recursion is here to show the block identity,
not because it is the quickest route.
"""

import numpy as np


def split_quadrants(matrix):
    """The four quadrants of an even-sided matrix, in reading order."""
    rows, columns = matrix.shape
    middle_row, middle_column = rows // 2, columns // 2
    return (matrix[:middle_row, :middle_column], matrix[:middle_row, middle_column:],
            matrix[middle_row:, :middle_column], matrix[middle_row:, middle_column:])


def trace_of_product(x, y):
    """tr(x @ y) by recursion on quadrants.

    Sizes must be powers of two. Odd sizes produce a zero-width quadrant that
    never reaches the scalar base case, which used to surface as a
    RecursionError rather than as a clear refusal.
    """
    x, y = np.asarray(x), np.asarray(y)
    if x.shape != y.shape or x.shape[0] != x.shape[1]:
        raise ValueError(f"expected two square matrices of equal size, got {x.shape} and {y.shape}")
    n = x.shape[0]
    if n < 1 or n & (n - 1):
        raise ValueError(f"size must be a power of two, got {n}")
    return _trace_of_product(x, y)


def _trace_of_product(x, y):
    if x.shape == (1, 1):
        return x[0, 0] * y[0, 0]
    x0, x1, x2, x3 = split_quadrants(x)
    y0, y1, y2, y3 = split_quadrants(y)
    return (_trace_of_product(x0, y0) + _trace_of_product(x1, y2) +
            _trace_of_product(x2, y1) + _trace_of_product(x3, y3))
