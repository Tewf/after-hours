# Flappy Bird AI (Convolutional Neural Network)

A deep learning project that trains a CNN-based policy to play Flappy Bird by processing raw pixel frames and learning optimal actions via REINFORCE (policy gradient).

## How It Works

1. **Environment** (`flappy_bird_env.py`) - A Pygame-based Flappy Bird game exposed as a Python generator. Each step yields an RGB frame and the current score, and accepts an action (0 = do nothing, 1 = flap).

2. **Policy Network** (`flappy_bird_qnn.ipynb`) - A 3-layer CNN that takes 84x84 grayscale frames as input and outputs action logits:
   - Conv2d(1, 16, 8, stride=4) -> Conv2d(16, 32, 4, stride=2) -> Conv2d(32, 32, 3) -> FC(3200, 256) -> FC(256, 2)

3. **Training** - REINFORCE with discounted returns, entropy regularization, and gradient clipping. Episodes are collected in batches, advantages are normalized, and the policy is updated end-to-end.

## Project Structure

```
Flappy_Bird_CNN/
├── flappy_bird_env.py       # Game environment (playable + generator mode)
├── flappy_bird_qnn.ipynb    # CNN policy, training loop, evaluation
├── flappy_bird_env.ipynb    # Environment exploration notebook
├── flappy_policy.pt         # Saved policy checkpoint
└── images/                  # Game sprites (bird, pipes, background, digits)
```

## Usage

### Play manually
```python
from flappy_bird_env import Run
Run()
```

### Train the AI
Run all cells in `flappy_bird_qnn.ipynb`. Training parameters:
- 500 epochs, 10 episodes per epoch
- Learning rate: 3e-4 (Adam)
- Discount factor (gamma): 0.99

### Evaluate a trained policy
```python
load_checkpoint(policy, optimizer, "flappy_policy.pt")
scores = evaluate(policy, episodes=10, render=True)
```

## Requirements

- Python 3.10+
- PyTorch
- Pygame
- OpenCV (`cv2`)
- Gymnasium
- NumPy
