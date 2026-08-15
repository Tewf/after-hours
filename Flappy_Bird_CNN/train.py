"""Train the policy with REINFORCE and a learned baseline.

    python train.py --epochs 2000 --ckpt-dir checkpoints --log-csv results/reinforce.csv

Resume from the last checkpoint with --resume. Everything is seeded, so a run
repeats given the same --seed.
"""

import os
import csv
import time
import random
import argparse

import numpy as np
import torch
import torch.nn.functional as F

from flappy_gym_env import make_env
from networks import ActorCritic, to_tensor


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=2000)
    parser.add_argument("--episodes-per-epoch", type=int, default=10)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--entropy-coef", type=float, default=0.02,
                        help="raised from 0.01: with two actions the policy went "
                             "near-deterministic by epoch 20 and stopped exploring")
    parser.add_argument("--frame-skip", type=int, default=2)
    parser.add_argument("--value-coef", type=float, default=0.5)
    parser.add_argument("--grad-clip", type=float, default=10.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=10000,
                        help="episode step cap, so a good policy cannot run forever")
    parser.add_argument("--ckpt-dir", default="checkpoints")
    parser.add_argument("--log-csv", default="results/reinforce.csv")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--eval-every", type=int, default=25)
    parser.add_argument("--eval-episodes", type=int, default=20)
    parser.add_argument("--target-pipes", type=float, default=10.0)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def discounted_returns(rewards, gamma, device):
    """Reverse scan.

    The original multiplied by gamma**t and divided it back out, which underflows
    in float32 on long episodes and returns inf once the agent starts surviving.
    """
    out = torch.empty(len(rewards), dtype=torch.float32, device=device)
    running = 0.0
    for t in range(len(rewards) - 1, -1, -1):
        running = rewards[t] + gamma * running
        out[t] = running
    return out


def run_episode(env, policy, device, max_steps, deterministic=False, grad=True):
    """One episode. Returns per-step tensors plus the pipes cleared."""
    observation, info = env.reset()
    log_probs, entropies, values, rewards = [], [], [], []
    pipes = 0
    with torch.set_grad_enabled(grad):
        for _ in range(max_steps):
            action, log_prob, entropy, value = policy.act(
                to_tensor(observation, device), deterministic=deterministic)
            observation, reward, terminated, truncated, info = env.step(action.item())
            log_probs.append(log_prob)
            entropies.append(entropy)
            values.append(value)
            rewards.append(reward)
            pipes = info["score"]
            if terminated or truncated:
                break
    return log_probs, entropies, values, rewards, pipes


def evaluate(env, policy, device, episodes, max_steps):
    """Greedy score over N episodes, which is what the target is measured on."""
    policy.eval()
    scores = []
    for _ in range(episodes):
        *_, pipes = run_episode(env, policy, device, max_steps,
                                deterministic=True, grad=False)
        scores.append(pipes)
    policy.train()
    return float(np.mean(scores)), float(np.std(scores)), max(scores)


def save_checkpoint(path, policy, optimizer, epoch, best):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    torch.save({"policy_state_dict": policy.state_dict(),
                "optim_state_dict": optimizer.state_dict(),
                "epoch": epoch, "best_pipes": best,
                "arch": "ActorCritic", "in_channels": 4}, path)


def main():
    args = parse_args()
    seed_everything(args.seed)
    device = torch.device(args.device)

    env = make_env(seed=args.seed, frame_skip=args.frame_skip)
    policy = ActorCritic(in_channels=4, n_actions=env.action_space.n).to(device)
    optimizer = torch.optim.Adam(policy.parameters(), lr=args.lr)

    start_epoch, best_pipes = 1, -1.0
    last_path = os.path.join(args.ckpt_dir, "last.pt")
    best_path = os.path.join(args.ckpt_dir, "best.pt")
    if args.resume and os.path.exists(last_path):
        state = torch.load(last_path, map_location=device)
        policy.load_state_dict(state["policy_state_dict"])
        optimizer.load_state_dict(state["optim_state_dict"])
        start_epoch, best_pipes = state["epoch"] + 1, state.get("best_pipes", -1.0)
        print(f"resumed from {last_path} at epoch {start_epoch}", flush=True)

    os.makedirs(os.path.dirname(os.path.abspath(args.log_csv)), exist_ok=True)
    new_log = not os.path.exists(args.log_csv)
    log_file = open(args.log_csv, "a", newline="")
    writer = csv.writer(log_file)
    if new_log:
        writer.writerow(["epoch", "avg_reward", "avg_pipes", "max_pipes",
                         "policy_loss", "value_loss", "entropy", "steps", "seconds"])

    started = time.time()
    for epoch in range(start_epoch, args.epochs + 1):
        batch_logp, batch_entropy, batch_value, batch_return = [], [], [], []
        episode_rewards, episode_pipes, steps = [], [], 0

        for _ in range(args.episodes_per_epoch):
            log_probs, entropies, values, rewards, pipes = run_episode(
                env, policy, device, args.max_steps)
            batch_logp.extend(log_probs)
            batch_entropy.extend(entropies)
            batch_value.extend(values)
            batch_return.append(discounted_returns(rewards, args.gamma, device))
            episode_rewards.append(sum(rewards))
            episode_pipes.append(pipes)
            steps += len(rewards)

        log_probs = torch.stack(batch_logp).squeeze(-1)
        entropies = torch.stack(batch_entropy).squeeze(-1)
        values = torch.stack(batch_value).squeeze(-1)
        returns = torch.cat(batch_return)

        # Standardise the returns before either head sees them. The rewards here
        # are +0.1 a frame, +1 a pipe and -10 for dying, so raw returns reach
        # about +-80 and their mean squared error reaches 21 while the policy
        # loss sits near 0.05. With a shared trunk and value_coef 0.5 that made
        # the value term 224 times the policy term, so the convolutions were
        # being trained almost entirely to regress returns. value_coef 0.5 is
        # borrowed from implementations that clip rewards to [-1, 1]; without
        # that clipping the coefficient has to be earned, not assumed.
        normalised_returns = (returns - returns.mean()) / (returns.std() + 1e-8)
        advantage = normalised_returns - values.detach()

        policy_loss = -(log_probs * advantage).mean()
        value_loss = F.mse_loss(values, normalised_returns)
        entropy = entropies.mean()
        loss = policy_loss + args.value_coef * value_loss - args.entropy_coef * entropy

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(policy.parameters(), args.grad_clip)
        optimizer.step()

        writer.writerow([epoch, f"{np.mean(episode_rewards):.3f}",
                         f"{np.mean(episode_pipes):.3f}", max(episode_pipes),
                         f"{policy_loss.item():.4f}", f"{value_loss.item():.4f}",
                         f"{entropy.item():.4f}", steps, f"{time.time() - started:.1f}"])
        log_file.flush()

        if epoch % 10 == 0:
            print(f"epoch {epoch}/{args.epochs}  reward {np.mean(episode_rewards):7.2f}  "
                  f"pipes {np.mean(episode_pipes):5.2f} (max {max(episode_pipes)})  "
                  f"entropy {entropy.item():.3f}  {steps} steps", flush=True)

        if epoch % args.eval_every == 0:
            mean, std, best = evaluate(env, policy, device,
                                       args.eval_episodes, args.max_steps)
            print(f"  eval @ {epoch}: {mean:.2f} +/- {std:.2f} pipes over "
                  f"{args.eval_episodes} episodes (best {best})", flush=True)
            if mean > best_pipes:
                best_pipes = mean
                save_checkpoint(best_path, policy, optimizer, epoch, best_pipes)
                print(f"  new best, saved to {best_path}", flush=True)
            save_checkpoint(last_path, policy, optimizer, epoch, best_pipes)
            if mean >= args.target_pipes:
                print(f"target of {args.target_pipes} pipes reached at epoch {epoch}", flush=True)
                break

    save_checkpoint(last_path, policy, optimizer, epoch, best_pipes)
    log_file.close()
    print(f"done. best eval {best_pipes:.2f} pipes, {(time.time() - started) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
