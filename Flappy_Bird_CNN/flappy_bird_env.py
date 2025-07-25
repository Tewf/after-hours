# %%
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
import sys
import random
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_SPACE, K_UP

# %%
def createPipe():
    offset = window_height/3
    pipeHeight = game_images['pipeimage'][0].get_height()
    
    # generating random height of pipes
    y2 = offset + random.randrange(
      0, int(window_height - game_images['sea_level'].get_height() - 1.2 * offset))  
    pipeX = window_width + 10
    y1 = pipeHeight - y2 + offset
    pipe = [
      
        # upper Pipe
        {'x': pipeX, 'y': -y1},
      
          # lower Pipe
        {'x': pipeX, 'y': y2}  
    ]
    return pipe

# %%
# Checking if bird is above the sealevel.
def isGameOver(horizontal, vertical, up_pipes, down_pipes):
    if vertical > elevation - 25 or vertical < 0: 
        return True

    # Checking if bird hits the upper pipe or not
    for pipe in up_pipes:    
        pipeHeight = game_images['pipeimage'][0].get_height()
        if(vertical < pipeHeight + pipe['y'] 
           and abs(horizontal - pipe['x']) < game_images['pipeimage'][0].get_width()):
            return True
          
    # Checking if bird hits the lower pipe or not
    for pipe in down_pipes:
        if (vertical + game_images['flappybird'].get_height() > pipe['y']) and abs(horizontal - pipe['x']) < game_images['pipeimage'][0].get_width():
            return True
    return False

# %%
def flappygame():
    your_score = 0
    horizontal = int(window_width/5)
    vertical = int(window_width/2)
    ground = 0
    mytempheight = 100

    # Generating two pipes for blitting on window
    first_pipe = createPipe()
    second_pipe = createPipe()

    # List containing lower pipes
    down_pipes = [
        {'x': window_width+300-mytempheight,
         'y': first_pipe[1]['y']},
        {'x': window_width+300-mytempheight+(window_width/2),
         'y': second_pipe[1]['y']},
    ]

    # List Containing upper pipes 
    up_pipes = [
        {'x': window_width+300-mytempheight,
         'y': first_pipe[0]['y']},
        {'x': window_width+200-mytempheight+(window_width/2),
         'y': second_pipe[0]['y']},
    ]

    pipeVelX = -4 #pipe velocity along x

    bird_velocity_y = -9  # bird velocity
    bird_Max_Vel_Y = 10   
    bird_Min_Vel_Y = -8
    birdAccY = 1
    
     # velocity while flapping
    bird_flap_velocity = -8
    
    # It is true only when the bird is flapping
    bird_flapped = False  
    while True:
       
        # Handling the key pressing events
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                if vertical > 0:
                    bird_velocity_y = bird_flap_velocity
                    bird_flapped = True

        # This function will return true if the flappybird is crashed
        game_over = isGameOver(horizontal, vertical, up_pipes, down_pipes)
        if game_over:
            # fill screen white on game over
            window.fill((255,255,255))
            pygame.display.update()
            pygame.time.delay(300)    # 1 second pause
            pygame.quit()
            sys.exit()
        # check for your_score
        playerMidPos = horizontal + game_images['flappybird'].get_width()/2
        for pipe in up_pipes:
            pipeMidPos = pipe['x'] + game_images['pipeimage'][0].get_width()/2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                  # Printing the score
                your_score += 1
                print(f"Your your_score is {your_score}")

        if bird_velocity_y < bird_Max_Vel_Y and not bird_flapped:
            bird_velocity_y += birdAccY

        if bird_flapped:
            bird_flapped = False
        playerHeight = game_images['flappybird'].get_height()
        vertical = vertical + min(bird_velocity_y, elevation - vertical - playerHeight)

        # move pipes to the left
        for upperPipe, lowerPipe in zip(up_pipes, down_pipes):
            upperPipe['x'] += pipeVelX
            lowerPipe['x'] += pipeVelX

        # Add a new pipe when the first is about
        # to cross the leftmost part of the screen
        if 0 < up_pipes[0]['x'] < 5:
            newpipe = createPipe()
            up_pipes.append(newpipe[0])
            down_pipes.append(newpipe[1])

        # if the pipe is out of the screen, remove it
        if up_pipes[0]['x'] < -game_images['pipeimage'][0].get_width():
            up_pipes.pop(0)
            down_pipes.pop(0)

        # Lets blit our game images now
        window.blit(game_images['background'], (0, 0))
        for upperPipe, lowerPipe in zip(up_pipes, down_pipes):
            window.blit(game_images['pipeimage'][0],
                        (upperPipe['x'], upperPipe['y']))
            window.blit(game_images['pipeimage'][1],
                        (lowerPipe['x'], lowerPipe['y']))

        window.blit(game_images['sea_level'], (ground, elevation))
        window.blit(game_images['flappybird'], (horizontal, vertical))
        
        # Fetching the digits of score.
        numbers = [int(x) for x in list(str(your_score))]
        width = 0
        
        # finding the width of score images from numbers.
        for num in numbers:
            width += game_images['scoreimages'][num].get_width()
        Xoffset = (window_width - width)/1.1
        
        # Blitting the images on the window.
        for num in numbers:
            window.blit(game_images['scoreimages'][num], (Xoffset, window_width*0.02))
            Xoffset += game_images['scoreimages'][num].get_width()
            
        # Refreshing the game window and displaying the score.
        pygame.display.update()
        
        # Set the framepersecond
        framepersecond_clock.tick(framepersecond)

# %%
def flappygame_generator(action=None):
    """
    A coroutine‐style generator:
    yields (frame, score) and accepts an action (0 or 1) sent in.
    If action==1, the bird flaps on that step.
    """
    your_score   = 0
    horizontal   = int(window_width / 5)
    vertical     = int(window_height / 2)
    ground       = 0
    mytempheight = 100

    # off‐screen canvas
    canvas = pygame.Surface((window_width, window_height))

    # initial pipes
    first_pipe, second_pipe = createPipe(), createPipe()
    down_pipes = [
        {'x': window_width + 300 - mytempheight,            'y': first_pipe[1]['y']},
        {'x': window_width + 300 - mytempheight + window_width//2, 'y': second_pipe[1]['y']},
    ]
    up_pipes = [
        {'x': window_width + 300 - mytempheight,            'y': first_pipe[0]['y']},
        {'x': window_width + 300 - mytempheight + window_width//2, 'y': second_pipe[0]['y']},
    ]

    pipeVelX           = -4
    bird_velocity_y    = -9
    bird_Max_Vel_Y     = 10
    birdAccY           = 1
    bird_flap_velocity = -8
    bird_flapped       = False

    while True:
        # handle quit events
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
                canvas.fill((255,255,255))
                arr = pygame.surfarray.array3d(canvas)
                arr = np.transpose(arr, (1,0,2))
                yield arr, your_score
                return

        # apply external action
        if action == 1 and vertical > 0:
            bird_velocity_y = bird_flap_velocity
            bird_flapped   = True

        # collision check
        if isGameOver(horizontal, vertical, up_pipes, down_pipes):
            canvas.fill((255,255,255))
            arr = pygame.surfarray.array3d(canvas)
            arr = np.transpose(arr, (1,0,2))
            yield arr, your_score
            return

        # update score
        player_mid = horizontal + game_images['flappybird'].get_width() / 2
        for p in up_pipes:
            pmid = p['x'] + game_images['pipeimage'][0].get_width() / 2
            if pmid <= player_mid < pmid + abs(pipeVelX):
                your_score += 1

        # physics
        if bird_velocity_y < bird_Max_Vel_Y and not bird_flapped:
            bird_velocity_y += birdAccY
        bird_flapped = False
        bh = game_images['flappybird'].get_height()
        vertical += min(bird_velocity_y, elevation - vertical - bh)

        # move & spawn pipes
        for u, d in zip(up_pipes, down_pipes):
            u['x'] += pipeVelX
            d['x'] += pipeVelX
        if 0 < up_pipes[0]['x'] < 5:
            np0, np1 = createPipe()
            up_pipes.append(np0);  down_pipes.append(np1)
        if up_pipes[0]['x'] < -game_images['pipeimage'][0].get_width():
            up_pipes.pop(0);     down_pipes.pop(0)

        # draw off‐screen
        canvas.blit(game_images['background'], (0, 0))
        for u, d in zip(up_pipes, down_pipes):
            canvas.blit(game_images['pipeimage'][0], (u['x'], u['y']))
            canvas.blit(game_images['pipeimage'][1], (d['x'], d['y']))
        canvas.blit(game_images['sea_level'], (ground, elevation))
        canvas.blit(game_images['flappybird'], (horizontal, vertical))

        # draw score
        nums = [int(c) for c in str(your_score)]
        total_w = sum(game_images['scoreimages'][n].get_width() for n in nums)
        x0 = (window_width - total_w) / 2
        for n in nums:
            img = game_images['scoreimages'][n]
            canvas.blit(img, (x0, window_height * 0.02))
            x0 += img.get_width()

        # cap FPS
        framepersecond_clock.tick(framepersecond)

        # grab frame & yield, receive next action
        arr = pygame.surfarray.array3d(canvas)
        arr = np.transpose(arr, (1,0,2))
        action = yield arr, your_score


# %%
def run_generator():
    """
    Drive flappygame_generator with real‐time key events,
    mirroring the behavior of Run().
    """
    global window, game_images, framepersecond, elevation
    global window_width, window_height,framepersecond_clock
    # game setup (same as in Run)
    window_width   = 600
    window_height  = 499
    elevation      = window_height * 0.8
    framepersecond = 32
    framepersecond_clock = pygame.time.Clock()

    pygame.init()
    window = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption('Flappy Bird (generator)')
    clock = pygame.time.Clock()

    # load images
    base = '/home/hamlil/Desktop/Flappy_Bird_CNN/images'
    game_images = {}
    game_images['scoreimages'] = tuple(
        pygame.image.load(f'{base}/{i}.png').convert_alpha()
        for i in range(10)
    )
    game_images['flappybird'] = pygame.image.load(f'{base}/bird.png').convert_alpha()
    game_images['sea_level']  = pygame.image.load(f'{base}/base.jfif').convert_alpha()
    game_images['background'] = pygame.image.load(f'{base}/background.jpg').convert_alpha()
    pi = pygame.image.load(f'{base}/pipe.png').convert_alpha()
    game_images['pipeimage']  = (
        pygame.transform.rotate(pi, 180),
        pi
    )

    # prime the generator
    gen = flappygame_generator(action=None)
    frame, score = next(gen)

    running = True
    while running:
        action = 0
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYDOWN and e.key == K_ESCAPE):
                running = False
            elif e.type == KEYDOWN and e.key in (K_SPACE, K_UP):
                action = 1

        try:
            frame, score = gen.send(action)
        except StopIteration:
            break

        # blit the frame returned by generator
        surf = pygame.surfarray.make_surface(frame.transpose(1,0,2))
        window.blit(surf, (0, 0))
        pygame.display.update()
        print(f"Score: {score}")

        clock.tick(framepersecond)

    pygame.quit()

# %%
# %%
# Global Variables for the game
def Run():
    global window, game_images, framepersecond, elevation
    global window_width, window_height,framepersecond_clock
    window_width = 600
    window_height = 499

    window = pygame.display.set_mode((window_width, window_height))   
    elevation = window_height * 0.8
    game_images = {}      
    framepersecond = 32
    framepersecond_clock = pygame.time.Clock()

    # File paths
    background_image   = '/home/hamlil/Desktop/Flappy_Bird_CNN/images/background.jpg'
    pipeimage          = '/home/hamlil/Desktop/Flappy_Bird_CNN/images/pipe.png'
    sealevel_image     = '/home/hamlil/Desktop/Flappy_Bird_CNN/images/base.jfif'
    birdplayer_image   = '/home/hamlil/Desktop/Flappy_Bird_CNN/images/bird.png'




    pygame.init()  
    framepersecond_clock = pygame.time.Clock()
    pygame.display.set_caption('Flappy Bird Game')      

        # Load all the images
    game_images['scoreimages'] = tuple(
            pygame.image.load(f'/home/hamlil/Desktop/Flappy_Bird_CNN/images/{i}.png').convert_alpha()
            for i in range(10)
        )
    game_images['flappybird'] = pygame.image.load(birdplayer_image).convert_alpha()                  
    game_images['sea_level'] = pygame.image.load(sealevel_image).convert_alpha()
    game_images['background'] = pygame.image.load(background_image).convert_alpha()
    game_images['pipeimage'] = (
            pygame.transform.rotate(pygame.image.load(pipeimage).convert_alpha(), 180),
            pygame.image.load(pipeimage).convert_alpha()
        )

    print("WELCOME TO THE FLAPPY BIRD GAME")
    print("Press space or up to start the game")
    pygame.time.delay(2000)
    flappygame()
        # Start screen loop
    while True:
        horizontal = int(window_width / 5)
        vertical = int((window_height - game_images['flappybird'].get_height()) / 2)
        ground = 0

        while True:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                elif event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                    flappygame()  # Start the game

                # Draw welcome screen
            window.blit(game_images['background'], (0, 0))
            window.blit(game_images['flappybird'], (horizontal, vertical))
            window.blit(game_images['sea_level'], (ground, elevation))
            pygame.display.update()
            framepersecond_clock.tick(framepersecond)

# %%
# %%
