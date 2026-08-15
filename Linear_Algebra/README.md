# Matrix algorithms from scratch

Four classical problems solved the long way round, to see what the shortcut is
hiding. NumPy appears throughout, but only as the oracle each result is checked
against, never as the implementation.

```sh
python test_linear_algebra.py     # 11 checks, under a second
```

| | |
|---|---|
| [`fft.py`](fft.py) · [`matrix_product.py`](matrix_product.py) | Radix-2 Cooley-Tukey in one and two dimensions, then `A @ B` assembled in the frequency domain without ever forming an outer product. Matches `numpy.fft` to 1e-13 at n=64 and `A @ B` to 1e-16 relative |
| [`determinant.py`](determinant.py) | Divide and conquer through the Schur complement, cofactors and all, with no call to `numpy.linalg.det`. Matches to 1e-13 at n=16 |
| [`exact_elimination.py`](exact_elimination.py) | Gauss-Jordan inversion in unbounded integer arithmetic, so the inverse is exact rather than nearly right. `A @ A_inverse` is exactly the identity, not close to it |
| [`product_trace.py`](product_trace.py) | tr(XY) by recursing on quadrants, O(n^2) instead of forming the O(n^3) product |

Each notebook narrates one module and plots what it claims:
[`fft_matrix_multiplication`](fft_matrix_multiplication.ipynb),
[`determinant_schur_complement`](determinant_schur_complement.ipynb),
[`exact_integer_inverse`](exact_integer_inverse.ipynb),
[`trace_without_the_product`](trace_without_the_product.ipynb).

## What these are not

None of them is fast. The frequency-domain product costs more than `A @ B`, the
determinant is far worse than an LU factorisation, and `numpy.sum(x * y.T)`
beats the recursive trace in one line. They are demonstrations of identities,
and each notebook plots its own cost so the gap is visible rather than implied.

## What was wrong before, and is recorded here on purpose

This folder previously had no tests, no plots and no assertions, and its prose
had been rewritten twice without re-running the code underneath it. What that
hid:

- The inverse transform called the **forward** transform on all four quadrants
  and carried a sign error, so it did not invert. A hand-tuned division by 4 at
  the call site made one 4x4 example look plausible.
- The 1D transform was demonstrated on a **length-7** input. Radix-2 has nothing
  to say about 7, so every entry except the DC term was wrong. Both transforms
  now refuse sizes that are not powers of two.
- A cell ended in `result == numpy.fft.fft2(...)` under a heading promising
  verification, and printed `False`. The transform was correct; the comparison
  was floating-point equality. It is `numpy.allclose` now.
- The determinant called `numpy.linalg.det` inside its cofactor loop, 112 times
  for a 16x16, which is precisely where "from scratch" mattered.
- The complexity claim was wrong three ways at once: a filename saying
  `n^log n`, the notebook's own text disowning it, and this README calling it
  sub-cubic. No bound is claimed now.
- The elimination had no pivoting, so a zero on the diagonal annihilated a row
  and returned an all-zero matrix for an invertible input. It was also `int64`,
  so exactness silently ended around n=8, and it stopped one step short of ever
  producing an inverse.

## Licence

[MIT](../LICENSE)
