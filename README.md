# Side Projects

Work I do outside coursework, in reinforcement learning, computer algebra,
numerical linear algebra and applied mathematical modelling. Each directory is
self-contained, with its own README and requirements.

---

## [Flappy Bird from raw pixels](Flappy_Bird_CNN/)

A convolutional policy network trained by REINFORCE on 84×84 grayscale frames,
with no access to game state — the agent sees only what a player would.
Architecture is three convolutional layers into two fully connected ones;
returns are discounted at γ = 0.99 and the policy is trained over 500 epochs.

**Python, PyTorch, Pygame, Gymnasium**

## [A 3-SAT decision procedure over GF(2)](Groebner_Basis_SAT_Solver/)

Clauses are encoded as polynomials in the Boolean ring GF(2)[x₁,…,xₙ]/(xᵢ²−xᵢ),
where satisfying assignments are exactly the common zeros. Triangular
Gröbner-style elimination propagates forced consequences; branching completes the
search.

Correctness is checked against exhaustive enumeration rather than only against a
reference solver: 500 instances at n = 8–12 and 2,000 at n = 20, with no
incorrect verdict and no invalid assignment. The write-up reports a negative
result as well — the elimination step is sound but detects almost no
unsatisfiable instance on its own, and the benchmark ratio m/n = 3.0 sits well
below the phase transition, so a high success rate there measures the instance
distribution rather than the solver.

**Python** · PySAT optional, for cross-checking against MiniSat

## [Matrix algorithms implemented from first principles](Linear_Algebra/)

Four notebooks, each rebuilding a standard result rather than calling it:

- multiplication in the frequency domain via the 2D FFT
- determinant in O(n^log n) by divide-and-conquer on the Schur complement
- trace of a product computed recursively, without forming the product
- Gaussian elimination in exact rational arithmetic, on LCM-scaled integers

**Python, NumPy**

## [Progressive income tax as a continuous model](Taxes/)

France's 2024 income tax schedule, modelled rather than tabulated: gross-to-net
conversion including social charges and CSG, exponential curve fitting per
bracket, and the Lambert W function used to locate the point where marginal
fiscal efficiency shifts — €62,114 gross.

**Python, SciPy, Matplotlib, Quarto**

## [Sorting algorithms as 3D animation](Blender_Python_Scripts/)

Bubble sort and merge sort driven through Blender's Python API, with bars
swapping, highlighting and translating so that each algorithm's access pattern
becomes visible.

**Python, Blender API**

---

## Licence

[MIT](LICENSE)
