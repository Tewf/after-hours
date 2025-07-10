# Gröbner‐Basis 3-SAT Solver over GF(2)

A from-scratch Python implementation of a 3-SAT decision procedure based on Gröbner‐basis (Hamlil elimination) techniques in the Boolean ring GF(2)\[x₁,…,xₙ]/⟨xᵢ²−xᵢ⟩.

<p align="center">
  <img src="https://img.shields.io/badge/language-Python-3.10-%23yellowgreen" alt="Python 3.10">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License">
</p>

---

## 🚀 Features

* **Polynomial encoding** of 3-SAT clauses as GF(2) ideals with idempotence xᵢ² = xᵢ
* **Triangular Gröbner‐like basis** extraction via monomial elimination + local one-variable forcing
* **Recursive backtracking** interleaving elimination with branching on free variables
* **Solver wrapper** for stress-testing against a reference SAT solver (e.g. PySAT’s Minisat)
* **Notebook demos** illustrating substitution, elimination, and monomial‐injection steps

---

## 📂 Repository Layout

```
groebner-sat/
├── polynomial.py        # GF(2) Polynomial class + monomial operations
├── utils.py             # sat_to_polynomials, generate_3sat, verify_solution
├── solver.py            # triangular_Grobner_Basis, local_test, polynomial_Solver
├── tests.py             # brute_decide + stress-test harness
├── examples/
│   ├── demo_small.py    # solve a tiny 3-SAT instance
│   └── Substitution.ipynb  # Jupyter notebook illustrating eliminate_var
└── README.md            # this document
```

---

## 🎯 Quickstart

1. **Clone** and install dependencies

   ```bash
   git clone https://github.com/yourname/groebner-sat.git
   cd groebner-sat
   pip install python-sat
   ```

2. **Solve a random 3-SAT**

   ```python
   from utils import generate_3sat, sat_to_polynomials
   from solver import polynomial_Solver, UnsatError

   NUM_VARS, NUM_CLAUSES = 20, 60
   clauses = generate_3sat(NUM_VARS, NUM_CLAUSES, seed=42)
   polys   = sat_to_polynomials(clauses, NUM_VARS)

   solution = polynomial_Solver(polys, NUM_VARS)
   if solution is None:
       print("UNSAT")
   else:
       print("SAT!  Assignment:", solution)
   ```

3. **Run the test suite**

   ```bash
   python tests.py
   ```

---

## 📖 Design Overview

### 1. Encoding 3-SAT → GF(2) Polynomials

Each clause $(ℓ₁∨ℓ₂∨ℓ₃)$ becomes

$$
  (1+x_i)\,(1+x_j)\,x_k = 0
$$

in GF(2), with $x_i=1$ for a positive literal and omitted for a negation.

### 2. Triangular Elimination & Local Test

* **`triangular_Grobner_Basis(polys, var_assign)`**
  Repeatedly selects the “largest” polynomial, applies forced single-variable assignments via `local_test()`, and records monomial‐to‐polynomial reductions.
* **`local_test(poly, var_assign)`**
  Randomly picks a variable in `poly`, tries setting it to 1 then 0; if either yields a contradiction $1=0$, forces the opposite and recurses.

### 3. Recursive Solver with Eliminate-Var

Once no more forced consequences remain, if not all variables are assigned, `polynomial_Solver` picks a free variable, **eliminates** it from the basis via `p.eliminate_var(v)`, and recurses.

---

## 📊 Performance & Complexity

* **Worst‐case** exponential in $n$, due to the number of monomial overlaps/S-polynomials up to degree ≤ n.
* **Practical** for small-to-medium random 3-SAT (n≈20–30, m≈60–100) as a demonstration and educational tool.

---

## 🤔 Suggestions & Future Work

* **Term-order Variants**: experiment with lex, graded-lex, etc.
* **Caching**: memoize reduced S-polynomials to avoid recomputation.
* **Heuristic Branching**: use VSIDS or clause-frequency heuristics.
* **Parallelization**: explore concurrent branching on multiple variables.
* **Benchmarking**: integrate SATLIB or DIMACS corpora.
* **Visualization**: extend the notebook to animate elimination steps.

---

## 🤝 Contributing

1. Fork the repo
2. Create a branch (`git checkout -b feature/foo`)
3. Commit your changes (`git commit -am 'Add foo'`)
4. Push and open a Pull Request

---

## 📜 License

MIT © Your Name
