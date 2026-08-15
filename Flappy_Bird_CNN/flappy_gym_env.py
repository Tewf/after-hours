"""A Gymnasium environment around the Pygame game, and the observation stack the agent learns from.

The single most important thing here is `FrameStackObservation(4)`. One 84x84
frame shows where the bird is but not which way it is moving, and in Flappy Bird
the correct action at a given height depends almost entirely on velocity. With a
single frame the optimal policy is not a function of the observation, so no
amount of training reaches it. Four stacked frames make velocity visible as
displacement.

Preprocessing is composed from Gymnasium's own wrappers rather than written
again by hand.
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces
from gymnasium.wrappers import (
    ResizeObservation,
    FrameStackObservation,
    MaxAndSkipObservation,
)

import flappy_bird_env as game

FRAME_SIZE = 84
STACK = 4
FRAME_SKIP = 2
ALIVE_REWARD = 0.1
PIPE_REWARD = 1.0
DEATH_REWARD = -10.0


class FlappyBirdEnv(gym.Env):
    """Raw RGB frames in, discrete flap/no-flap out.

    Observations are the rendered frame only. The pipe count is returned in
    `info` for logging and is never given to the agent.
    """

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 32}

    def __init__(self, render_mode=None, headless=True):
        super().__init__()
        game.init_pygame("Flappy Bird", headless=headless and render_mode != "human")
        self.render_mode = render_mode
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(
            low=0, high=255,
            shape=(game.window_height, game.window_width, 3), dtype=np.uint8)
        self._generator = None
        self._last_frame = None
        self._score = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            game.random.seed(seed)
        self._generator = game.flappygame_generator(
            action=None, realtime=self.render_mode == "human")
        frame, score, _ = next(self._generator)
        self._last_frame, self._score = frame, score
        return frame, {"score": score}

    def step(self, action):
        previous_score = self._score
        try:
            frame, score, done = self._generator.send(int(action))
        except StopIteration:
            # The generator already yielded its terminal frame; treat a further
            # step as terminal rather than letting the exception escape.
            return self._last_frame, DEATH_REWARD, True, False, {"score": self._score}

        self._last_frame, self._score = frame, score
        if done:
            reward = DEATH_REWARD
        else:
            reward = ALIVE_REWARD + PIPE_REWARD * (score - previous_score)
        return frame, reward, done, False, {"score": score}

    def render(self):
        return self._last_frame

    def close(self):
        self._generator = None


class BlueChannelObservation(gym.ObservationWrapper):
    """Reduce to one channel by taking blue, not by converting to luminance.

    Measured on the sprites against the sky background, in levels out of 255:

        projection            bird vs sky   pipe vs sky
        luminance greyscale            22            64
        blue channel                  181           247

    The bird is yellow on light blue and the two are nearly equiluminant, so the
    standard greyscale conversion very nearly erases the one object whose
    position the agent most needs to know. Its own body came through at 22
    levels while the obstacles came through at 64.

    This is a fixed, hand-chosen projection in the same sense greyscaling is.
    The agent still receives nothing but rendered pixels.
    """

    def __init__(self, env):
        super().__init__(env)
        height, width, _ = env.observation_space.shape
        self.observation_space = spaces.Box(
            low=0, high=255, shape=(height, width), dtype=np.uint8)

    def observation(self, observation):
        return observation[:, :, 2]


def make_env(render_mode=None, headless=True, seed=None, frame_skip=FRAME_SKIP):
    """The environment as the agent sees it: 4 stacked 84x84 single-channel frames.

    The channel is taken before the resize, so the resize works on one plane
    rather than three.

    frame_skip holds each action for several game frames and sums the reward
    over them. The game runs at 32 fps, so without it the agent makes about 35
    decisions before its first pipe and has to assign credit across all of them.
    """
    env = FlappyBirdEnv(render_mode=render_mode, headless=headless)
    env = BlueChannelObservation(env)
    env = ResizeObservation(env, (FRAME_SIZE, FRAME_SIZE))
    if frame_skip > 1:
        env = MaxAndSkipObservation(env, skip=frame_skip)
    env = FrameStackObservation(env, STACK)
    if seed is not None:
        env.reset(seed=seed)
    return env


if __name__ == "__main__":
    import time

    env = make_env(seed=0)
    observation, info = env.reset(seed=0)
    print("observation shape:", observation.shape, observation.dtype)
    print("observation space:", env.observation_space)

    start, steps = time.time(), 0
    observation, info = env.reset(seed=0)
    terminated = False
    while not terminated and steps < 2000:
        observation, reward, terminated, truncated, info = env.step(env.action_space.sample())
        steps += 1
    elapsed = time.time() - start
    print(f"{steps} steps in {elapsed:.2f}s = {steps / elapsed:,.0f} steps/s "
          f"(the old realtime cap was 32/s)")
