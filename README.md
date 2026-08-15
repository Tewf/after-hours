# Side Projects

> [Lire en français](README.fr.md)

Things I build in my own time, in machine learning, computer algebra and applied
mathematics. Each folder stands alone, with its own README and requirements.

| Project | What it is |
|---|---|
| [Flappy Bird from raw pixels](Flappy_Bird_CNN/) | REINFORCE with a value baseline, and a DQN for comparison. Both learn from four stacked 84×84 frames and never see the game state. *PyTorch, Pygame, Gymnasium* |
| [3-SAT solver over GF(2)](Groebner_Basis_SAT_Solver/) | Clauses become polynomials; triangular Gröbner-style elimination propagates, branching finishes. Checked against exhaustive search on 2,500 instances. *Python* |
| [Matrix algorithms from scratch](Linear_Algebra/) | Multiplication by 2D FFT, determinant in O(n^log n), trace of a product without the product, exact-rational Gaussian elimination. *Python, NumPy* |
| [French income tax, modelled](Taxes/) | Exponential fits per bracket, then Lambert W to find the tipping point, at €62,114 gross. *SciPy, Quarto* |
| [Sorting algorithms in 3D](Blender_Python_Scripts/) | Bubble and merge sort animated and rendered through Blender's Python API. *Blender* |

## Running any of them

```sh
cd <folder>
pip install -r requirements.txt
```

Each folder's README says what to run from there. The Blender scripts load in
Blender's Scripting workspace instead.

## Licence

[MIT](LICENSE)
