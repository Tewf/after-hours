"""The two networks, sharing one convolutional trunk so the comparison is about the algorithm.

Both read the same input: 4 stacked 84x84 greyscale frames. The trunk is the one
the project started with, with its paddings kept; only the heads differ.

    Conv2d(4, 16, k8, s4, p2)   84 -> 21
    Conv2d(16, 32, k4, s2, p1)  21 -> 10
    Conv2d(32, 32, k3, s1, p1)  10 -> 10
    Linear(3200, 256)
"""

import torch
import torch.nn as nn

TRUNK_FEATURES = 32 * 10 * 10


def _trunk(in_channels):
    return nn.Sequential(
        nn.Conv2d(in_channels, 16, 8, 4, 2), nn.ReLU(),
        nn.Conv2d(16, 32, 4, 2, 1), nn.ReLU(),
        nn.Conv2d(32, 32, 3, 1, 1), nn.ReLU(),
        nn.Flatten(),
        nn.Linear(TRUNK_FEATURES, 256), nn.ReLU(),
    )


class ActorCritic(nn.Module):
    """Policy head plus a value head used only as a baseline.

    The value head does not bootstrap. Returns stay full Monte Carlo, and V(s)
    is subtracted from them to cut the variance of the gradient estimate. That
    is REINFORCE with baseline, not actor-critic: without it the advantage is a
    single scalar per batch, so a doomed state and a promising one get the same
    correction and the update mostly encodes where in the episode a step fell.
    """

    def __init__(self, in_channels=4, n_actions=2):
        super().__init__()
        self.trunk = _trunk(in_channels)
        self.policy_head = nn.Linear(256, n_actions)
        self.value_head = nn.Linear(256, 1)

    def forward(self, observation):
        features = self.trunk(observation)
        return self.policy_head(features), self.value_head(features).squeeze(-1)

    def act(self, observation, deterministic=False):
        """Sample an action, returning it with its log-probability and value."""
        logits, value = self(observation)
        distribution = torch.distributions.Categorical(logits=logits)
        action = logits.argmax(dim=-1) if deterministic else distribution.sample()
        return action, distribution.log_prob(action), distribution.entropy(), value


class DQN(nn.Module):
    """One Q value per action, off the same trunk."""

    def __init__(self, in_channels=4, n_actions=2):
        super().__init__()
        self.trunk = _trunk(in_channels)
        self.head = nn.Linear(256, n_actions)

    def forward(self, observation):
        return self.head(self.trunk(observation))


def to_tensor(observation, device):
    """uint8 (..., 4, 84, 84) frames to a float tensor scaled to [0, 1]."""
    tensor = torch.as_tensor(observation, dtype=torch.float32, device=device) / 255.0
    return tensor if tensor.dim() == 4 else tensor.unsqueeze(0)
