"""Radix-2 Cooley-Tukey transforms, written out rather than called from a library.

One butterfly serves both directions. The forward and inverse transforms differ
only in the sign of the exponent and in a single normalisation applied once at
the top, which is why they are one function here: writing the inverse out a
second time is how the earlier version of this file ended up with an inverse
that did not invert.

Everything is verified against `numpy.fft` in `test_linear_algebra.py`, to about
1e-13 at n = 32. NumPy is the oracle, not the implementation.

Sizes must be powers of two. Radix-2 has nothing to say about other lengths, and
silently returning a half-filled array is worse than refusing.
"""

import numpy as np


def _require_power_of_two(n, what):
    if n < 1 or n & (n - 1):
        raise ValueError(f"{what} must be a power of two, got {n}")


def fft_1d(x, sign=-1):
    """One-dimensional transform. sign=-1 forward, sign=+1 unnormalised inverse."""
    x = np.asarray(x, dtype=complex)
    _require_power_of_two(x.shape[0], "input length")
    return _fft_1d(x, sign)


def _fft_1d(x, sign):
    n = x.shape[0]
    if n == 1:
        return x.copy()
    even, odd = _fft_1d(x[::2], sign), _fft_1d(x[1::2], sign)
    twiddle = np.exp(sign * 2j * np.pi / n) ** np.arange(n // 2)
    return np.concatenate([even + twiddle * odd, even - twiddle * odd])


def _fft_2d(x, sign):
    """Both axes at once: split into even/odd rows and columns, four sub-transforms."""
    n = x.shape[0]
    if n == 1:
        return x.copy()
    even_even = _fft_2d(x[::2, ::2], sign)
    even_odd = _fft_2d(x[::2, 1::2], sign)
    odd_even = _fft_2d(x[1::2, ::2], sign)
    odd_odd = _fft_2d(x[1::2, 1::2], sign)
    return _butterfly_2d(even_even, even_odd, odd_even, odd_odd, n, sign)


def _butterfly_2d(even_even, even_odd, odd_even, odd_odd, n, sign):
    """Combine the four sub-transforms. Shared with the matrix product."""
    root = np.exp(sign * 2j * np.pi / n)
    row = root ** np.arange(n // 2)[:, None]
    column = root ** np.arange(n // 2)[None, :]
    y = np.zeros((n, n), dtype=complex)
    y[:n // 2, :n // 2] = even_even + column * even_odd + row * odd_even + row * column * odd_odd
    y[:n // 2, n // 2:] = even_even - column * even_odd + row * odd_even - row * column * odd_odd
    y[n // 2:, :n // 2] = even_even + column * even_odd - row * odd_even - row * column * odd_odd
    y[n // 2:, n // 2:] = even_even - column * even_odd - row * odd_even + row * column * odd_odd
    return y


def fft_2d(x):
    """Two-dimensional forward transform, matching `numpy.fft.fft2`."""
    x = np.asarray(x, dtype=complex)
    _require_power_of_two(x.shape[0], "input size")
    return _fft_2d(x, -1)


def inverse_fft_2d(x):
    """Two-dimensional inverse, matching `numpy.fft.ifft2`.

    The 1/n^2 is applied once here rather than per level. Folding it into the
    recursion is what produced the stray division by 4 that the earlier version
    needed at its call site to look right on one 4x4 example.
    """
    x = np.asarray(x, dtype=complex)
    _require_power_of_two(x.shape[0], "input size")
    return _fft_2d(x, +1) / (x.shape[0] ** 2)


def fft_along(a, axis):
    """Transform every row (axis=1) or every column (axis=0)."""
    a = np.asarray(a, dtype=complex)
    if axis == 0:
        return np.stack([fft_1d(a[:, c]) for c in range(a.shape[1])], axis=1)
    return np.stack([fft_1d(a[r, :]) for r in range(a.shape[0])], axis=0)
