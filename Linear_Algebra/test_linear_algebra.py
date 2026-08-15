"""Checks for every algorithm in this folder. Stdlib and numpy only.

    python test_linear_algebra.py

NumPy is used as the oracle, never as the implementation: each module computes
its own answer and is then compared against `numpy.fft`, `numpy.linalg` or the
plain definition. Every claim the READMEs make about this folder is checked here.
"""

import time
from fractions import Fraction

import numpy as np

from fft import fft_1d, fft_2d, inverse_fft_2d
from matrix_product import fast_matrix_multiplication
from determinant import determinant, SingularLeadingBlock
from exact_elimination import inverse, to_float, elimination_multipliers
from product_trace import trace_of_product

SIZES = (2, 4, 8, 16)
rng = np.random.default_rng(0)


def test_fft_matches_numpy():
    for n in SIZES + (32,):
        vector = rng.random(n) + 1j * rng.random(n)
        matrix = rng.random((n, n)) + 1j * rng.random((n, n))
        assert np.allclose(fft_1d(vector), np.fft.fft(vector)), n
        assert np.allclose(fft_2d(matrix), np.fft.fft2(matrix)), n
        assert np.allclose(inverse_fft_2d(matrix), np.fft.ifft2(matrix)), n
        assert np.allclose(inverse_fft_2d(fft_2d(matrix)), matrix), n


def test_fft_refuses_non_power_of_two():
    for bad in (3, 5, 7, 12):
        for call in (lambda: fft_1d(np.ones(bad)), lambda: fft_2d(np.ones((bad, bad)))):
            try:
                call()
            except ValueError:
                continue
            raise AssertionError(f"size {bad} should have been refused")


def test_matrix_product_matches_numpy():
    for n in SIZES:
        a, b = rng.integers(0, 50, (n, n)), rng.integers(0, 50, (n, n))
        assert np.allclose(fast_matrix_multiplication(a, b), a @ b), n


def test_determinant_matches_numpy():
    for n in (2, 3, 4, 5, 6, 8, 12):
        matrix = rng.random((n, n))
        assert np.isclose(determinant(matrix), np.linalg.det(matrix), rtol=1e-9), n


def test_determinant_reports_a_singular_leading_block():
    matrix = np.array([[0.0, 0.0, 1.0, 2.0], [0.0, 0.0, 3.0, 4.0],
                       [1.0, 2.0, 0.0, 0.0], [3.0, 5.0, 0.0, 0.0]])
    try:
        determinant(matrix)
    except SingularLeadingBlock:
        return
    raise AssertionError("a singular leading block should raise, not divide by zero")


def test_inverse_is_exact():
    for n in (3, 4, 6, 8, 10):
        matrix = rng.integers(-9, 10, (n, n))
        while round(np.linalg.det(matrix)) == 0:
            matrix = rng.integers(-9, 10, (n, n))
        computed = inverse(matrix)
        assert all(isinstance(value, Fraction) for row in computed for value in row)
        product = np.array(matrix, dtype=object) @ computed
        for i in range(n):
            for j in range(n):
                assert product[i, j] == (1 if i == j else 0), (n, i, j)
        assert np.allclose(to_float(computed), np.linalg.inv(matrix)), n


def test_inverse_pivots_past_a_zero_on_the_diagonal():
    """This matrix is invertible and used to come back as all zeros."""
    matrix = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
    product = np.array(matrix, dtype=object) @ inverse(matrix)
    assert np.array_equal(product, np.eye(3, dtype=object))


def test_inverse_refuses_a_singular_matrix():
    try:
        inverse(np.array([[1, 2], [2, 4]]))
    except ValueError:
        return
    raise AssertionError("a singular matrix should be refused")


def test_elimination_multipliers_cancel():
    for entry, pivot in ((4, 6), (7, 7), (-3, 12), (5, 1)):
        scale_entry, scale_pivot = elimination_multipliers(entry, pivot)
        assert scale_entry * entry - scale_pivot * pivot == 0, (entry, pivot)


def test_trace_matches_numpy():
    for n in SIZES:
        x, y = rng.random((n, n)), rng.random((n, n))
        assert np.isclose(trace_of_product(x, y), np.trace(x @ y)), n
        assert np.isclose(trace_of_product(x, y), np.sum(x * y.T)), n


def test_trace_refuses_non_power_of_two():
    for bad in (3, 5, 6):
        try:
            trace_of_product(rng.random((bad, bad)), rng.random((bad, bad)))
        except ValueError:
            continue
        raise AssertionError(f"size {bad} should have been refused")


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    started = time.time()
    for test in tests:
        test()
        print(f"  ok  {test.__name__}")
    print(f"\n{len(tests)} tests passed in {time.time() - started:.1f}s")
