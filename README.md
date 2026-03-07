# Side Projects & Creative Experiments

A collection of small, experimental projects built out of curiosity — spanning algorithms, game AI, mathematical computing, and data visualization.

> These are informal and often work-in-progress. The goal is exploration and learning. Feedback and ideas are always welcome!

---

## Projects

### [Flappy Bird CNN](Flappy_Bird_CNN/)
A deep learning project that trains a CNN to play Flappy Bird by processing raw pixel frames and learning optimal actions via REINFORCE policy gradient.

**Tech:** Python, PyTorch, Pygame, Gymnasium

### [Groebner-Basis 3-SAT Solver](Groebner_Basis_SAT_Solver/)
A from-scratch 3-SAT decision procedure using triangular Groebner-basis techniques in the Boolean ring GF(2)[x1,...,xn]. On 10,000 random instances (n=20, m=60), the elimination step alone flags ~99.94% of UNSAT cases without branching.

**Tech:** Python, PySAT (for benchmarking)

### [Linear Algebra Explorations](Linear_Algebra/)
Four notebooks implementing matrix algorithms from scratch:
- **Matrix multiplication via 2D FFT** — multiply in the frequency domain
- **Determinant in O(n^log n)** — divide-and-conquer via Schur complement
- **Recursive Tr(AB)** — compute trace without forming the full product
- **Gaussian elimination with exact fractions** — LCM-based integer arithmetic

**Tech:** Python, NumPy

### [Blender Sorting Visualizations](Blender_Python_Scripts/)
3D animations of sorting algorithms (bubble sort, merge sort) built with Blender's Python API. Bars swap, highlight, and move in real-time to visualize each algorithm's behavior.

**Tech:** Python, Blender API

### [French Income Tax Analysis](Taxes/)
Mathematical analysis of France's 2024 progressive income tax: exponential curve fitting per bracket, and Lambert W function to find the fiscal "tipping point" (~62k gross) where marginal efficiency shifts.

**Tech:** Python, SciPy, Matplotlib, Quarto

---

## Repository Structure

```
.
├── Flappy_Bird_CNN/             # CNN-based Flappy Bird AI
├── Groebner_Basis_SAT_Solver/   # Algebraic 3-SAT solver
├── Linear_Algebra/              # Matrix algorithm notebooks
├── Blender_Python_Scripts/      # 3D sorting visualizations
└── Taxes/                       # French tax modeling
```

## License

[MIT](LICENSE)
