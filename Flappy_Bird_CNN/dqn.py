"""Train the same trunk with DQN, as a second opinion on the policy gradient.

    python dqn.py --steps 400000 --ckpt-dir checkpoints/dqn --log-csv results/dqn.csv

Value learning against policy gradient on identical observations, so any
difference is the algorithm rather than the inputs. Replay buffer, target
network, epsilon-greedy exploration, Huber loss.

This replaces an abandoned DQN that sat unreachable in a notebook: it used
Sigmoid activations throughout, and greyscaled its input to one channel only to
repeat it back to three for a Conv2d(3, ...). Neither survives here.
"""

import os
import csv
import time
import random
import argparse
from collections import deque

import numpy as np
import torch
import torch.nn.functional as F

from flappy_gym_env import make_env
from networks import DQN, to_tensor


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=400_000)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--buffer-size", type=int, default=80_000,
                        help="80k stacked uint8 frames is about 2.1 GB of RAM")
    parser.add_argument("--learning-starts", type=int, default=5_000)
    parser.add_argument("--train-every", type=int, default=4)
    parser.add_argument("--target-sync", type=int, default=1_000)
    parser.add_argument("--epsilon-start", type=float, default=1.0)
    parser.add_argument("--epsilon-end", type=float, default=0.02)
    parser.add_argument("--epsilon-decay-steps", type=int, default=100_000)
    parser.add_argument("--grad-clip", type=float, default=10.0)
    parser.add_argument("--frame-skip", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=10_000)
    parser.add_argument("--ckpt-dir", default="checkpoints/dqn")
    parser.add_argument("--log-csv", default="results/dqn.csv")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--eval-every", type=int, default=20_000)
    parser.add_argument("--eval-episodes", type=int, default=20)
    parser.add_argument("--target-pipes", type=float, default=10.0)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


class ReplayBuffer:
    """Uniform replay over uint8 frames, on the CPU to spare the 8 GB of VRAM.

    Each observation is stored once, not twice. The next observation of step t
    is simply the observation of step t+1, so keeping both doubles memory for
    nothing: at 100k transitions of 4x84x84 that is 5.2 GB against 2.6 GB, and
    this machine has 16 GB with a browser and Blender in it.

    The one index that cannot be sampled is the most recent write, whose
    successor has not been stored yet. When done[i] is set the successor is the
    next episode's reset frame, which is harmless because the bootstrap term is
    masked by (1 - done).
    """

    def __init__(self, capacity, observation_shape):
        self.observations = np.zeros((capacity, *observation_shape), dtype=np.uint8)
        self.actions = np.zeros(capacity, dtype=np.int64)
        self.rewards = np.zeros(capacity, dtype=np.float32)
        self.dones = np.zeros(capacity, dtype=np.float32)
        self.capacity = capacity
        self.index = 0
        self.size = 0

    def push(self, observation, action, reward, done):
        self.observations[self.index] = observation
        self.actions[self.index] = action
        self.rewards[self.index] = reward
        self.dones[self.index] = done
        self.index = (self.index + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size, device):
        newest = (self.index - 1) % self.capacity
        indices = np.random.randint(0, self.size, size=batch_size)
        indices[indices == newest] = (newest - 1) % max(self.size, 2)
        following = (indices + 1) % self.size
        return (
            to_tensor(self.observations[indices], device),
            torch.as_tensor(self.actions[indices], dtype=torch.int64, device=device),
            torch.as_tensor(self.rewards[indices], dtype=torch.float32, device=device),
            to_tensor(self.observations[following], device),
            torch.as_tensor(self.dones[indices], dtype=torch.float32, device=device),
        )

    def __len__(self):
        return self.size


def epsilon_at(step, args):
    fraction = min(1.0, step / args.epsilon_decay_steps)
    return args.epsilon_start + fraction * (args.epsilon_end - args.epsilon_start)


def evaluate(env, network, device, episodes, max_steps):
    """Greedy score over N episodes, the same measure train.py reports."""
    network.eval()
    scores = []
    with torch.no_grad():
        for _ in range(episodes):
            observation, info = env.reset()
            for _ in range(max_steps):
                action = int(network(to_tensor(observation, device)).argmax(dim=-1).item())
                observation, _, terminated, truncated, info = env.step(action)
                if terminated or truncated:
                    break
            scores.append(info["score"])
    network.train()
    return float(np.mean(scores)), float(np.std(scores)), max(scores)


def save_checkpoint(path, network, optimizer, step, best):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    torch.save({"policy_state_dict": network.state_dict(),
                "optim_state_dict": optimizer.state_dict(),
                "step": step, "best_pipes": best,
                "arch": "DQN", "in_channels": 4}, path)


def main():
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    device = torch.device(args.device)

    env = make_env(seed=args.seed, frame_skip=args.frame_skip)
    n_actions = env.action_space.n
    online = DQN(in_channels=4, n_actions=n_actions).to(device)
    target = DQN(in_channels=4, n_actions=n_actions).to(device)
    target.load_state_dict(online.state_dict())
    optimizer = torch.optim.Adam(online.parameters(), lr=args.lr)
    replay = ReplayBuffer(args.buffer_size, env.observation_space.shape)

    start_step, best_pipes = 0, -1.0
    last_path = os.path.join(args.ckpt_dir, "last.pt")
    best_path = os.path.join(args.ckpt_dir, "best.pt")
    if args.resume and os.path.exists(last_path):
        state = torch.load(last_path, map_location=device)
        online.load_state_dict(state["policy_state_dict"])
        target.load_state_dict(state["policy_state_dict"])
        optimizer.load_state_dict(state["optim_state_dict"])
        start_step, best_pipes = state["step"], state.get("best_pipes", -1.0)
        print(f"resumed from {last_path} at step {start_step}")

    os.makedirs(os.path.dirname(os.path.abspath(args.log_csv)), exist_ok=True)
    new_log = not os.path.exists(args.log_csv)
    log_file = open(args.log_csv, "a", newline="")
    writer = csv.writer(log_file)
    if new_log:
        writer.writerow(["step", "episode", "avg_reward", "avg_pipes", "max_pipes",
                         "loss", "epsilon", "seconds"])

    observation, info = env.reset()
    episode_reward, episode_steps, episode = 0.0, 0, 0
    recent_rewards, recent_pipes = deque(maxlen=50), deque(maxlen=50)
    recent_loss = deque(maxlen=100)
    started = time.time()

    for step in range(start_step, args.steps):
        epsilon = epsilon_at(step, args)
        if random.random() < epsilon:
            action = env.action_space.sample()
        else:
            with torch.no_grad():
                action = int(online(to_tensor(observation, device)).argmax(dim=-1).item())

        next_observation, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        replay.push(observation, action, reward, float(done))
        observation = next_observation
        episode_reward += reward
        episode_steps += 1

        if done or episode_steps >= args.max_steps:
            recent_rewards.append(episode_reward)
            recent_pipes.append(info["score"])
            episode += 1
            observation, info = env.reset()
            episode_reward, episode_steps = 0.0, 0

        if len(replay) >= args.learning_starts and step % args.train_every == 0:
            observations, actions, rewards, next_observations, dones = \
                replay.sample(args.batch_size, device)
            q_values = online(observations).gather(1, actions.unsqueeze(1)).squeeze(1)
            with torch.no_grad():
                bootstrap = target(next_observations).max(dim=1).values
                targets = rewards + args.gamma * bootstrap * (1.0 - dones)
            loss = F.smooth_l1_loss(q_values, targets)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(online.parameters(), args.grad_clip)
            optimizer.step()
            recent_loss.append(loss.item())

        if step % args.target_sync == 0:
            target.load_state_dict(online.state_dict())

        if step % 2000 == 0 and recent_pipes:
            writer.writerow([step, episode, f"{np.mean(recent_rewards):.3f}",
                             f"{np.mean(recent_pipes):.3f}", max(recent_pipes),
                             f"{np.mean(recent_loss):.4f}" if recent_loss else "",
                             f"{epsilon:.3f}", f"{time.time() - started:.1f}"])
            log_file.flush()
            print(f"step {step}/{args.steps}  episodes {episode}  "
                  f"reward {np.mean(recent_rewards):7.2f}  pipes {np.mean(recent_pipes):5.2f} "
                  f"(max {max(recent_pipes)})  eps {epsilon:.3f}")

        if step > 0 and step % args.eval_every == 0:
            mean, std, best = evaluate(env, online, device,
                                       args.eval_episodes, args.max_steps)
            print(f"  eval @ {step}: {mean:.2f} +/- {std:.2f} pipes (best {best})")
            if mean > best_pipes:
                best_pipes = mean
                save_checkpoint(best_path, online, optimizer, step, best_pipes)
                print(f"  new best, saved to {best_path}")
            save_checkpoint(last_path, online, optimizer, step, best_pipes)
            observation, info = env.reset()
            episode_reward, episode_steps = 0.0, 0
            if mean >= args.target_pipes:
                print(f"target of {args.target_pipes} pipes reached at step {step}")
                break

    save_checkpoint(last_path, online, optimizer, step, best_pipes)
    log_file.close()
    print(f"done. best eval {best_pipes:.2f} pipes, {(time.time() - started) / 60:.1f} min")


if __name__ == "__main__":
    main()
