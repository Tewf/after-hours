"""Matrix multiplication routed through the frequency domain.

A @ B is the sum over i of (column i of A) outer (row i of B). Each of those
outer products is rank one, and the transform of a sum is the sum of the
transforms, so the whole product can be assembled in the frequency domain
without ever forming an outer product. That is what `outer_sum_transform` does:
it carries the two vector families down the same radix-2 recursion the FFT uses
and only multiplies scalars at the leaves.

This is a demonstration, not a fast multiplication. It costs more than `A @ B`
and the point is the identity, not the speed. `test_linear_algebra.py` checks it
against `A @ B` to about 1e-16 relative.
"""

import numpy as np

from fft import fft_along, inverse_fft_2d, _butterfly_2d, _require_power_of_two


def outer_sum_transform(columns, rows):
    """Transform of sum_i outer(columns[i], rows[i]), never forming the sum.

    `columns` and `rows` are both (k, n): k vector pairs of length n.
    """
    n = columns.shape[1]
    if n == 1:
        return np.array([[np.sum(columns[:, 0] * rows[:, 0])]], dtype=complex)
    return _butterfly_2d(
        outer_sum_transform(columns[:, ::2], rows[:, ::2]),
        outer_sum_transform(columns[:, ::2], rows[:, 1::2]),
        outer_sum_transform(columns[:, 1::2], rows[:, ::2]),
        outer_sum_transform(columns[:, 1::2], rows[:, 1::2]),
        n, -1)


def fast_matrix_multiplication(a, b):
    """A @ B via the hand-written transforms in `fft.py`.

    Inverting along one axis of each operand leaves the pair in the domain where
    `outer_sum_transform`'s forward recursion lands exactly on the product.
    """
    a, b = np.asarray(a), np.asarray(b)
    _require_power_of_two(a.shape[0], "matrix size")
    if a.shape[1] != b.shape[0]:
        raise ValueError(f"shapes {a.shape} and {b.shape} do not multiply")
    a_transformed = fft_along(inverse_fft_2d(a), axis=1)
    b_transformed = fft_along(inverse_fft_2d(b), axis=0)
    return outer_sum_transform(a_transformed.T, b_transformed)
