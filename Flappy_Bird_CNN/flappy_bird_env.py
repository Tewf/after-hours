# %%
import os
import numpy as np
import pygame
import sys
import random
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_SPACE, K_UP

# ---- Global state (set by init_pygame) ----
window = None
game_images = {}
_initialized = False
window_width = 600
window_height = 499
elevation = 0
framepersecond = 32
framepersecond_clock = None

# ---- Constants ----
PIPE_VEL_X = -4
BIRD_GRAVITY = 1
BIRD_FLAP_VEL = -8
BIRD_MAX_VEL = 10
BIRD_INIT_VEL = -9
PIPE_OFFSET = 100

# %%
def init_pygame(title='Flappy Bird', headless=False, force=False):
    """Initialize pygame, set globals, and load all images.

    Idempotent: training calls this once per episode, and reopening the window
    plus reloading fifteen sprites each time cost more than the network did.
    Pass headless=True to run with no display (SDL's dummy driver still
    satisfies set_mode and convert_alpha, which the sprite loading needs).
    """
    global window, game_images, window_width, window_height
    global elevation, framepersecond, framepersecond_clock, _initialized

    if _initialized and not force:
        return

    window_width = 600
    window_height = 499
    elevation = window_height * 0.8
    framepersecond = 32

    if headless:
        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

    pygame.init()
    framepersecond_clock = pygame.time.Clock()
    window = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption(title)

    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
    game_images = {}
    game_images['scoreimages'] = tuple(
        pygame.image.load(os.path.join(base, f'{i}.png')).convert_alpha()
        for i in range(10)
    )
    game_images['flappybird'] = pygame.image.load(os.path.join(base, 'bird.png')).convert_alpha()
    game_images['sea_level'] = pygame.image.load(os.path.join(base, 'base.jfif')).convert_alpha()
    game_images['background'] = pygame.image.load(os.path.join(base, 'background.jpg')).convert_alpha()
    pipe_img = pygame.image.load(os.path.join(base, 'pipe.png')).convert_alpha()
    game_images['pipeimage'] = (pygame.transform.rotate(pipe_img, 180), pipe_img)
    _initialized = True

# %%
def _create_pipe():
    """Generate a random upper/lower pipe pair off-screen to the right."""
    offset = window_height / 3
    pipe_h = game_images['pipeimage'][0].get_height()
    y2 = offset + random.randrange(
        0, int(window_height - game_images['sea_level'].get_height() - 1.2 * offset))
    pipe_x = window_width + 10
    y1 = pipe_h - y2 + offset
    return {'x': pipe_x, 'y': -y1}, {'x': pipe_x, 'y': y2}

def _init_pipes():
    """Create the initial two pipe pairs."""
    up1, down1 = _create_pipe()
    up2, down2 = _create_pipe()
    start_x = window_width + 300 - PIPE_OFFSET
    up_pipes = [
        {'x': start_x, 'y': up1['y']},
        {'x': start_x + window_width // 2, 'y': up2['y']},
    ]
    down_pipes = [
        {'x': start_x, 'y': down1['y']},
        {'x': start_x + window_width // 2, 'y': down2['y']},
    ]
    return up_pipes, down_pipes

# %%
def _is_game_over(bird_x, bird_y, up_pipes, down_pipes):
    """Check if bird has hit the ground, ceiling, or any pipe."""
    if bird_y > elevation - 25 or bird_y < 0:
        return True

    pipe_w = game_images['pipeimage'][0].get_width()
    pipe_h = game_images['pipeimage'][0].get_height()
    bird_h = game_images['flappybird'].get_height()

    for pipe in up_pipes:
        if bird_y < pipe_h + pipe['y'] and abs(bird_x - pipe['x']) < pipe_w:
            return True

    for pipe in down_pipes:
        if (bird_y + bird_h > pipe['y']) and abs(bird_x - pipe['x']) < pipe_w:
            return True

    return False

# %%
def _update_physics(bird_y, bird_vel, flapped):
    """Apply gravity/flap and clamp to ground. Returns new (bird_y, bird_vel)."""
    if bird_vel < BIRD_MAX_VEL and not flapped:
        bird_vel += BIRD_GRAVITY
    bird_h = game_images['flappybird'].get_height()
    bird_y += min(bird_vel, elevation - bird_y - bird_h)
    return bird_y, bird_vel

def _update_pipes(up_pipes, down_pipes):
    """Move pipes left, spawn new ones, remove off-screen ones."""
    for u, d in zip(up_pipes, down_pipes):
        u['x'] += PIPE_VEL_X
        d['x'] += PIPE_VEL_X

    if 0 < up_pipes[0]['x'] < 5:
        new_up, new_down = _create_pipe()
        up_pipes.append(new_up)
        down_pipes.append(new_down)

    if up_pipes[0]['x'] < -game_images['pipeimage'][0].get_width():
        up_pipes.pop(0)
        down_pipes.pop(0)

def _check_score(bird_x, up_pipes):
    """Return 1 if the bird just passed a pipe, else 0."""
    bird_mid = bird_x + game_images['flappybird'].get_width() / 2
    for p in up_pipes:
        pipe_mid = p['x'] + game_images['pipeimage'][0].get_width() / 2
        if pipe_mid <= bird_mid < pipe_mid + abs(PIPE_VEL_X):
            return 1
    return 0

def _draw_frame(surface, bird_x, bird_y, up_pipes, down_pipes, score):
    """Render one frame of the game onto the given surface."""
    surface.blit(game_images['background'], (0, 0))
    for u, d in zip(up_pipes, down_pipes):
        surface.blit(game_images['pipeimage'][0], (u['x'], u['y']))
        surface.blit(game_images['pipeimage'][1], (d['x'], d['y']))
    surface.blit(game_images['sea_level'], (0, elevation))
    surface.blit(game_images['flappybird'], (bird_x, bird_y))

    # draw score digits
    digits = [int(c) for c in str(score)]
    total_w = sum(game_images['scoreimages'][d].get_width() for d in digits)
    x = (window_width - total_w) / 2
    for d in digits:
        img = game_images['scoreimages'][d]
        surface.blit(img, (x, window_height * 0.02))
        x += img.get_width()

# %%
def flappygame():
    """Interactive game loop — play with keyboard (Space/Up to flap)."""
    score = 0
    bird_x = int(window_width / 5)
    bird_y = int(window_height / 2)
    bird_vel = BIRD_INIT_VEL
    flapped = False
    up_pipes, down_pipes = _init_pipes()

    while True:
        # handle input
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key in (K_SPACE, K_UP):
                if bird_y > 0:
                    bird_vel = BIRD_FLAP_VEL
                    flapped = True

        if _is_game_over(bird_x, bird_y, up_pipes, down_pipes):
            window.fill((255, 255, 255))
            pygame.display.update()
            pygame.time.delay(300)
            return  # return to caller instead of sys.exit()

        score += _check_score(bird_x, up_pipes)
        bird_y, bird_vel = _update_physics(bird_y, bird_vel, flapped)
        flapped = False
        _update_pipes(up_pipes, down_pipes)
        _draw_frame(window, bird_x, bird_y, up_pipes, down_pipes, score)

        pygame.display.update()
        framepersecond_clock.tick(framepersecond)

# %%
def flappygame_generator(action=None, realtime=True):
    """
    A coroutine-style generator for AI training.
    Yields (frame, score, done) and accepts an action (0 or 1) via .send().
    If action==1, the bird flaps on that step.

    realtime=False drops the frame-rate cap. The cap lives inside this loop, so
    with it on every training step is limited to 32 per second no matter how
    fast the policy runs. Leave it on only when a human is watching.
    """
    score = 0
    bird_x = int(window_width / 5)
    bird_y = int(window_height / 2)
    bird_vel = BIRD_INIT_VEL
    flapped = False
    up_pipes, down_pipes = _init_pipes()

    canvas = pygame.Surface((window_width, window_height))

    def _grab_frame():
        # pixels3d is a direct view; array3d converts pixel by pixel and costs
        # 7.2 ms a frame here against 0.9 ms, which at training rates dominates
        # everything else the step does.
        view = pygame.surfarray.pixels3d(canvas)
        frame = np.transpose(view, (1, 0, 2)).copy()
        del view  # releases the surface lock
        return frame

    while True:
        # handle quit events
        if realtime:
            for e in pygame.event.get():
                if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
                    canvas.fill((255, 255, 255))
                    yield _grab_frame(), score, True
                    return

        # apply external action
        if action == 1 and bird_y > 0:
            bird_vel = BIRD_FLAP_VEL
            flapped = True

        # collision check
        if _is_game_over(bird_x, bird_y, up_pipes, down_pipes):
            canvas.fill((255, 255, 255))
            yield _grab_frame(), score, True
            return

        score += _check_score(bird_x, up_pipes)
        bird_y, bird_vel = _update_physics(bird_y, bird_vel, flapped)
        flapped = False
        _update_pipes(up_pipes, down_pipes)
        _draw_frame(canvas, bird_x, bird_y, up_pipes, down_pipes, score)

        if realtime:
            framepersecond_clock.tick(framepersecond)
        action = yield _grab_frame(), score, False

# %%
def run_generator():
    """Drive flappygame_generator with real-time key events."""
    init_pygame('Flappy Bird (generator)')
    gen = flappygame_generator(action=None)
    frame, score, done = next(gen)

    running = True
    while running and not done:
        action = 0
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
                running = False
            elif e.type == KEYDOWN and e.key in (K_SPACE, K_UP):
                action = 1

        try:
            frame, score, done = gen.send(action)
        except StopIteration:
            break

        surf = pygame.surfarray.make_surface(frame.transpose(1, 0, 2))
        window.blit(surf, (0, 0))
        pygame.display.update()
        framepersecond_clock.tick(framepersecond)

    pygame.quit()

# %%
def Run():
    """Main entry point: shows welcome screen, then plays on keypress."""
    init_pygame('Flappy Bird Game')

    print("WELCOME TO THE FLAPPY BIRD GAME")
    print("Press space or up to start the game")
    pygame.time.delay(2000)
    flappygame()

    # Welcome screen loop (replay after game over)
    bird_x = int(window_width / 5)
    bird_y = int((window_height - game_images['flappybird'].get_height()) / 2)

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN and event.key in (K_SPACE, K_UP):
                flappygame()

        window.blit(game_images['background'], (0, 0))
        window.blit(game_images['flappybird'], (bird_x, bird_y))
        window.blit(game_images['sea_level'], (0, elevation))
        pygame.display.update()
        framepersecond_clock.tick(framepersecond)
