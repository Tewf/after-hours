"""Determinant by divide and conquer, using the Schur complement.

Split the matrix into four blocks and the determinant of the whole follows from
the determinant of one block and a smaller determinant:

    det(M) = det(D*a - C @ adj(A) @ B) / a^(k-1),   a = det(A), A is k by k

Nothing here calls `numpy.linalg.det`. The earlier version did, inside the
cofactor loop, 112 times for a 16x16 matrix, which made "from scratch" untrue in
the one place it mattered. The cost of doing it honestly is that this is slow:
the cofactor step alone is O(n^2) minors of size n-1, so the recursion is far
worse than the O(n^3) of an LU factorisation. It is a demonstration of the
identity, not a way to compute determinants.

The file used to be named for a complexity bound its own text disowned. There is
no bound claimed here.
"""

import numpy as np


class SingularLeadingBlock(Exception):
    """The top-left block is singular, so the identity divides by zero.

    Not a property of the matrix, only of how it was split. A row swap fixes it,
    which this implementation deliberately does not do so the failure stays visible.
    """


def _augment_to_even(matrix):
    """Pad an odd size by one, with a 1 on the diagonal. The determinant is unchanged."""
    n = matrix.shape[0]
    augmented = np.zeros((n + 1, n + 1), dtype=matrix.dtype)
    augmented[:n, :n] = matrix
    augmented[n, n] = 1
    return augmented


def cofactor_matrix(matrix):
    """Cofactors, each one a determinant computed by this module."""
    n = matrix.shape[0]
    cofactors = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            minor = np.delete(np.delete(matrix, i, axis=0), j, axis=1)
            cofactors[i, j] = ((-1) ** (i + j)) * determinant(minor)
    return cofactors


def determinant(matrix):
    """Determinant of a square matrix."""
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"expected a square matrix, got shape {matrix.shape}")

    n = matrix.shape[0]
    if n == 0:
        return 1.0
    if n == 1:
        return matrix[0, 0]
    if n == 2:
        return matrix[0, 0] * matrix[1, 1] - matrix[0, 1] * matrix[1, 0]

    if n % 2:
        matrix = _augment_to_even(matrix)
        n += 1
    half = n // 2

    upper_left = matrix[:half, :half]
    upper_right = matrix[:half, half:]
    lower_left = matrix[half:, :half]
    lower_right = matrix[half:, half:]

    leading = determinant(upper_left)
    if leading == 0:
        raise SingularLeadingBlock(
            f"the {half}x{half} leading block is singular, so the Schur identity "
            f"cannot divide by its determinant")

    adjugate = cofactor_matrix(upper_left).T
    schur = lower_right * leading - lower_left @ (adjugate @ upper_right)
    return determinant(schur) / (leading ** (half - 1))
