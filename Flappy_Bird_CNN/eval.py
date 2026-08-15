"""Score a trained checkpoint, and optionally record it playing.

    python eval.py --checkpoint checkpoints/reinforce/best.pt --episodes 20
    python eval.py --checkpoint checkpoints/dqn/best.pt --record flappy.webp

The previous version of this returned an empty list: `scores` was initialised
and never appended to, so the README's own usage snippet ended in a
ZeroDivisionError and no score for the trained agent was ever recorded.
"""

import argparse

import numpy as np
import torch

from flappy_gym_env import make_env
from networks import ActorCritic, DQN, to_tensor


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--max-steps", type=int, default=10_000)
    parser.add_argument("--frame-skip", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--render", action="store_true", help="watch it in a window")
    parser.add_argument("--record", default=None,
                        help="write the best episode to this .webp or .gif")
    parser.add_argument("--record-fps", type=int, default=24)
    parser.add_argument("--record-width", type=int, default=None,
                        help="downscale the recording, which is 600 px wide otherwise")
    parser.add_argument("--record-max-frames", type=int, default=None,
                        help="truncate the recording; a good agent plays for "
                             "thousands of frames and the file grows with it")
    parser.add_argument("--record-quality", type=int, default=60,
                        help="WebP quality; the game background is photographic "
                             "and does not compress like flat artwork does")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def load_network(path, device, n_actions):
    state = torch.load(path, map_location=device)
    architecture = state.get("arch", "ActorCritic")
    network = (DQN if architecture == "DQN" else ActorCritic)(
        in_channels=state.get("in_channels", 4), n_actions=n_actions).to(device)
    network.load_state_dict(state["policy_state_dict"])
    network.eval()
    return network, architecture


def greedy_action(network, architecture, observation, device):
    if architecture == "DQN":
        return int(network(to_tensor(observation, device)).argmax(dim=-1).item())
    action, *_ = network.act(to_tensor(observation, device), deterministic=True)
    return int(action.item())


def play_episode(env, network, architecture, device, max_steps, capture=False):
    observation, info = env.reset()
    frames = [env.render()] if capture else None
    with torch.no_grad():
        for _ in range(max_steps):
            action = greedy_action(network, architecture, observation, device)
            observation, _, terminated, truncated, info = env.step(action)
            if capture:
                frames.append(env.render())
            if terminated or truncated:
                break
    return info["score"], frames


def main():
    args = parse_args()
    device = torch.device(args.device)
    env = make_env(render_mode="human" if args.render else None,
                   seed=args.seed, frame_skip=args.frame_skip)
    network, architecture = load_network(args.checkpoint, device, env.action_space.n)
    print(f"{architecture} from {args.checkpoint} on {device}")

    scores, best_frames, best_score = [], None, -1
    for episode in range(args.episodes):
        capture = args.record is not None
        score, frames = play_episode(env, network, architecture, device,
                                     args.max_steps, capture=capture)
        scores.append(score)
        if capture and score > best_score:
            best_score, best_frames = score, frames
        print(f"  episode {episode + 1:>3}: {score} pipes")

    print(f"\n{np.mean(scores):.2f} +/- {np.std(scores):.2f} pipes over "
          f"{args.episodes} episodes (min {min(scores)}, max {max(scores)})")

    if args.record and best_frames:
        import imageio.v3 as iio
        if args.record_max_frames:
            best_frames = best_frames[:args.record_max_frames]
        if args.record_width:
            import cv2
            height, width = best_frames[0].shape[:2]
            size = (args.record_width, round(height * args.record_width / width))
            best_frames = [cv2.resize(f, size, interpolation=cv2.INTER_AREA)
                           for f in best_frames]
        iio.imwrite(args.record, np.stack(best_frames),
                    duration=int(1000 / args.record_fps), loop=0,
                    quality=args.record_quality, method=6)
        print(f"wrote {args.record}: best episode, {best_score} pipes, "
              f"{len(best_frames)} frames")


if __name__ == "__main__":
    main()
