import pygame
import sys
import random
import os
import math

# Initialize Pygame
pygame.init()
# Initialize mixer for sound
pygame.mixer.init()

# --- SOUND SETUP ---
# Place your .wav or .ogg files in the same directory as this script
HIT_SOUND = os.path.join(os.path.dirname(__file__), 'hit.wav')
SCORE_SOUND = os.path.join(os.path.dirname(__file__), 'score.wav')
POWERUP_SOUND = os.path.join(os.path.dirname(__file__), 'powerup.wav')
MUSIC = os.path.join(os.path.dirname(__file__), 'music.ogg')

def play_sound(sound):
    try:
        pygame.mixer.Sound(sound).play()
    except Exception:
        pass  # Ignore if file not found

# Start background music (looping)
try:
    pygame.mixer.music.load(MUSIC)
    pygame.mixer.music.play(-1)
except Exception:
    pass  # Ignore if file not found

# Screen dimensions
WIDTH, HEIGHT = 480, 320  # Smaller window for corner play
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Quick Pong Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Paddle settings
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 100
PLAYER_X = 30
AI_X = WIDTH - 30 - PADDLE_WIDTH
PADDLE_SPEED = 7

# Ball settings
BALL_SIZE = 20
BALL_SPEED_X = 6 * random.choice((1, -1))
BALL_SPEED_Y = 6 * random.choice((1, -1))

# Score
player_score = 0
ai_score = 0
FONT = pygame.font.SysFont("Arial", 36)

# Paddle and ball rectangles
player = pygame.Rect(PLAYER_X, HEIGHT//2 - PADDLE_HEIGHT//2, PADDLE_WIDTH, PADDLE_HEIGHT)
ai = pygame.Rect(AI_X, HEIGHT//2 - PADDLE_HEIGHT//2, PADDLE_WIDTH, PADDLE_HEIGHT)
ball = pygame.Rect(WIDTH//2 - BALL_SIZE//2, HEIGHT//2 - BALL_SIZE//2, BALL_SIZE, BALL_SIZE)

# --- POWER-UP SYSTEM ---
POWERUP_SIZE = 20
POWERUP_TYPES = ["speed", "grow", "shrink", "split", "slow"]
powerup = None
powerup_type = None
powerup_timer = 0
POWERUP_DURATION = 300  # frames
powerup_active = False
powerup_effect_timer = 0

# Crazy mode variables
CRAZY_MODE_CHANCE = 0.005  # 0.5% chance per frame
CRAZY_MODE_TIMER = 0
CRAZY_MODE_DURATION = 60  # frames
crazy_mode_active = False

# Two-player mode flag
TWO_PLAYER = False

# --- ACHIEVEMENTS ---
win_streak = 0
max_win_streak = 0
perfect_game = False
achievement_message = ""
achievement_timer = 0
ACHIEVEMENT_DISPLAY = 120  # frames

# --- CHALLENGE MODE ---
difficulty_level = 1
challenge_message = ""
challenge_timer = 0
CHALLENGE_DISPLAY = 90  # frames

# --- SKINS & THEMES ---
THEMES = [
    {"bg": (0,0,0), "paddle": (255,255,255), "ball": (255,255,255)},
    {"bg": (30,30,60), "paddle": (0,255,255), "ball": (255,255,0)},
    {"bg": (50,0,50), "paddle": (255,0,255), "ball": (0,255,0)},
    {"bg": (255,255,255), "paddle": (0,0,0), "ball": (0,0,255)},
]
current_theme = 0

# --- LEADERBOARD ---
LEADERBOARD_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'leaderboard.txt')
high_score = 0

def load_high_score():
    global high_score
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            high_score = int(f.read().strip())
    except Exception:
        high_score = 0

def save_high_score():
    with open(LEADERBOARD_FILE, 'w') as f:
        f.write(str(high_score))

def randomize_ball_angle(speed_x, speed_y, axis):
    # axis: 'x' for vertical paddle, 'y' for horizontal paddle
    if axis == 'x':
        # For vertical paddles (left/right), reverse X direction and add some Y randomness
        new_speed_x = -speed_x
        new_speed_y = speed_y + random.uniform(-2, 2)
    else:
        # For horizontal paddles (top/bottom), reverse Y direction and add some X randomness
        new_speed_x = speed_x + random.uniform(-2, 2)
        new_speed_y = -speed_y
    
    # Ensure minimum speed
    if abs(new_speed_x) < 3:
        new_speed_x = 3 if new_speed_x > 0 else -3
    if abs(new_speed_y) < 3:
        new_speed_y = 3 if new_speed_y > 0 else -3
    
    return new_speed_x, new_speed_y

def reset_ball():
    global BALL_SPEED_X, BALL_SPEED_Y, high_score, win_streak, max_win_streak, perfect_game, achievement_message, achievement_timer, difficulty_level, challenge_message, challenge_timer, PADDLE_SPEED
    ball.center = (WIDTH//2, HEIGHT//2)
    BALL_SPEED_X = 6 * random.choice((1, -1)) * difficulty_level
    BALL_SPEED_Y = 6 * random.choice((1, -1)) * difficulty_level
    play_sound(SCORE_SOUND)
    # Update high score
    if player_score > high_score:
        high_score = player_score
        save_high_score()
    if ai_score > high_score:
        high_score = ai_score
        save_high_score()
    # Achievements
    if player_score == 0 and ai_score > 0:
        win_streak = 0
        perfect_game = False
    if ai_score == 0 and player_score > 0:
        win_streak += 1
        if win_streak > max_win_streak:
            max_win_streak = win_streak
            achievement_message = f"Win Streak! {win_streak}"
            achievement_timer = ACHIEVEMENT_DISPLAY
        if player_score >= 5:
            perfect_game = True
            achievement_message = "Perfect Game!"
            achievement_timer = ACHIEVEMENT_DISPLAY
    # Challenge mode: increase difficulty every 15 points (was 5)
    if not vector_mode and (player_score + ai_score) // 15 + 1 > difficulty_level:
        difficulty_level += 1
        challenge_message = f"Level Up! Difficulty {difficulty_level}"
        challenge_timer = CHALLENGE_DISPLAY
        global obstacle_speed, PADDLE_SPEED, PADDLE_HEIGHT
        # Increase speeds gently
        obstacle_speed = min(obstacle_speed + OBSTACLE_SPEED_INCREMENT, MAX_BALL_SPEED)
        PADDLE_SPEED = min(PADDLE_SPEED + PADDLE_SPEED_INCREMENT, MAX_PADDLE_SPEED)
        # Shrink paddles gently
        PADDLE_HEIGHT = max(int(PADDLE_HEIGHT * 0.95), MIN_PADDLE_HEIGHT)
        player.height = PADDLE_HEIGHT
        ai.height = PADDLE_HEIGHT
        # For four-player mode paddles (horizontal):
        paddle_left.height = PADDLE_HEIGHT
        paddle_right.height = PADDLE_HEIGHT
        paddle_top.width = max(int(paddle_top.width * 0.95), MIN_PADDLE_HEIGHT)
        paddle_bottom.width = max(int(paddle_bottom.width * 0.95), MIN_PADDLE_HEIGHT)

# Add variable to track last paddle to touch ball
last_paddle_touched = "player"  # "player", "ai", "left", "right", "top", "bottom"

# Make power-ups more frequent
def spawn_powerup():
    global powerup, powerup_type, powerup_timer
    if random.randint(0, 90) == 0 and not powerup:  # ~once every 1.5 seconds (was 3 seconds)
        x = random.randint(WIDTH//4, WIDTH*3//4)
        y = random.randint(40, HEIGHT-40)
        powerup = pygame.Rect(x, y, POWERUP_SIZE, POWERUP_SIZE)
        powerup_type = random.choice(POWERUP_TYPES)
        powerup_timer = 300  # frames

def draw_powerup():
    if powerup:
        color = (0,255,0) if powerup_type == "speed" else (0,0,255) if powerup_type == "grow" else (255,0,0)
        pygame.draw.rect(WIN, color, powerup)

# Update power-up effects to apply to the correct paddle:
def handle_powerup_collision():
    global powerup, powerup_type, BALL_SPEED_X, BALL_SPEED_Y, PADDLE_HEIGHT, powerup_active, powerup_effect_timer
    global display_powerup_banner, powerup_banner_text, powerup_banner_timer, split_active, split_balls, split_timer
    if powerup and ball.colliderect(powerup):
        if powerup_type == "speed":
            BALL_SPEED_X *= 1.5
            BALL_SPEED_Y *= 1.5
            powerup_banner_text = "Speed Boost!"
        elif powerup_type == "grow":
            # Apply to the paddle that last touched the ball
            if four_player_mode:
                if last_paddle_touched == "left":
                    paddle_left.height = int(paddle_left.height * 1.5)
                    powerup_banner_text = "Left Paddle Grows!"
                elif last_paddle_touched == "right":
                    paddle_right.height = int(paddle_right.height * 1.5)
                    powerup_banner_text = "Right Paddle Grows!"
                elif last_paddle_touched == "top":
                    paddle_top.width = int(paddle_top.width * 1.5)
                    powerup_banner_text = "Top Paddle Grows!"
                elif last_paddle_touched == "bottom":
                    paddle_bottom.width = int(paddle_bottom.width * 1.5)
                    powerup_banner_text = "Bottom Paddle Grows!"
            else:
                if last_paddle_touched == "player":
                    player.height = int(player.height * 1.5)
                    powerup_banner_text = "Your Paddle Grows!"
                else:
                    ai.height = int(ai.height * 1.5)
                    powerup_banner_text = "AI Paddle Grows!"
        elif powerup_type == "shrink":
            # Apply to the opponent of the paddle that last touched the ball
            if four_player_mode:
                if last_paddle_touched == "left":
                    # Shrink a random opponent paddle
                    opponent_paddles = ["right", "top", "bottom"]
                    target = random.choice(opponent_paddles)
                    if target == "right":
                        paddle_right.height = max(20, int(paddle_right.height * 0.5))
                        powerup_banner_text = "Right Paddle Shrinks!"
                    elif target == "top":
                        paddle_top.width = max(20, int(paddle_top.width * 0.5))
                        powerup_banner_text = "Top Paddle Shrinks!"
                    elif target == "bottom":
                        paddle_bottom.width = max(20, int(paddle_bottom.width * 0.5))
                        powerup_banner_text = "Bottom Paddle Shrinks!"
                elif last_paddle_touched == "right":
                    opponent_paddles = ["left", "top", "bottom"]
                    target = random.choice(opponent_paddles)
                    if target == "left":
                        paddle_left.height = max(20, int(paddle_left.height * 0.5))
                        powerup_banner_text = "Left Paddle Shrinks!"
                    elif target == "top":
                        paddle_top.width = max(20, int(paddle_top.width * 0.5))
                        powerup_banner_text = "Top Paddle Shrinks!"
                    elif target == "bottom":
                        paddle_bottom.width = max(20, int(paddle_bottom.width * 0.5))
                        powerup_banner_text = "Bottom Paddle Shrinks!"
                elif last_paddle_touched == "top":
                    opponent_paddles = ["left", "right", "bottom"]
                    target = random.choice(opponent_paddles)
                    if target == "left":
                        paddle_left.height = max(20, int(paddle_left.height * 0.5))
                        powerup_banner_text = "Left Paddle Shrinks!"
                    elif target == "right":
                        paddle_right.height = max(20, int(paddle_right.height * 0.5))
                        powerup_banner_text = "Right Paddle Shrinks!"
                    elif target == "bottom":
                        paddle_bottom.width = max(20, int(paddle_bottom.width * 0.5))
                        powerup_banner_text = "Bottom Paddle Shrinks!"
                elif last_paddle_touched == "bottom":
                    opponent_paddles = ["left", "right", "top"]
                    target = random.choice(opponent_paddles)
                    if target == "left":
                        paddle_left.height = max(20, int(paddle_left.height * 0.5))
                        powerup_banner_text = "Left Paddle Shrinks!"
                    elif target == "right":
                        paddle_right.height = max(20, int(paddle_right.height * 0.5))
                        powerup_banner_text = "Right Paddle Shrinks!"
                    elif target == "top":
                        paddle_top.width = max(20, int(paddle_top.width * 0.5))
                        powerup_banner_text = "Top Paddle Shrinks!"
            else:
                if last_paddle_touched == "player":
                    ai.height = max(20, int(ai.height * 0.5))
                    powerup_banner_text = "AI Paddle Shrinks!"
                else:
                    player.height = max(20, int(player.height * 0.5))
                    powerup_banner_text = "Your Paddle Shrinks!"
        elif powerup_type == "split":
            split_active = True
            split_timer = SPLIT_DURATION
            split_balls.clear()
            # Create 2 extra balls with slightly different angles
            for angle in [-0.3, 0.3]:
                vx = BALL_SPEED_X * math.cos(angle) - BALL_SPEED_Y * math.sin(angle)
                vy = BALL_SPEED_X * math.sin(angle) + BALL_SPEED_Y * math.cos(angle)
                split_balls.append({"rect": ball.copy(), "vx": vx, "vy": vy})
            powerup_banner_text = "Ball Split!"
        elif powerup_type == "slow":
            # Slow down all balls by 30%
            BALL_SPEED_X *= 0.7
            BALL_SPEED_Y *= 0.7
            for b in split_balls:
                b["vx"] *= 0.7
                b["vy"] *= 0.7
            powerup_banner_text = "Ball Slowed Down!"
        powerup = None
        powerup_active = True
        powerup_effect_timer = POWERUP_DURATION
        play_sound(POWERUP_SOUND)
        display_powerup_banner = True
        powerup_banner_timer = POWERUP_BANNER_DURATION

def update_powerup():
    global powerup, powerup_timer, BALL_SPEED_X, BALL_SPEED_Y, player, ai, powerup_active, powerup_effect_timer
    global display_powerup_banner, powerup_banner_timer, split_active, split_balls, split_timer
    if powerup:
        powerup_timer -= 1
        if powerup_timer <= 0:
            powerup = None
    if powerup_active:
        powerup_effect_timer -= 1
        if powerup_effect_timer <= 0:
            # Reset effects
            global PADDLE_HEIGHT
            BALL_SPEED_X = 6 * (1 if BALL_SPEED_X > 0 else -1)
            BALL_SPEED_Y = 6 * (1 if BALL_SPEED_Y > 0 else -1)
            player.height = PADDLE_HEIGHT
            ai.height = PADDLE_HEIGHT
            powerup_active = False
    if display_powerup_banner:
        powerup_banner_timer -= 1
        if powerup_banner_timer <= 0:
            display_powerup_banner = False
    if split_active:
        split_timer -= 1
        if split_timer <= 0:
            split_active = False
            split_balls.clear()

# --- OBSTACLE ---
obstacle = pygame.Rect(WIDTH//2 - 15, HEIGHT//2 - 40, 30, 80)
obstacle_speed = 3
obstacle_dir = 1

def move_obstacle():
    global obstacle, obstacle_dir
    obstacle.y += obstacle_speed * obstacle_dir
    if obstacle.top <= 0 or obstacle.bottom >= HEIGHT:
        obstacle_dir *= -1

def handle_obstacle_collision():
    global BALL_SPEED_X
    if ball.colliderect(obstacle):
        BALL_SPEED_X *= -1

def draw():
    theme = THEMES[current_theme]
    WIN.fill(theme["bg"])
    pygame.draw.rect(WIN, theme["paddle"], player)
    pygame.draw.rect(WIN, theme["paddle"], ai)
    pygame.draw.ellipse(WIN, theme["ball"], ball)
    pygame.draw.aaline(WIN, theme["paddle"], (WIDTH//2, 0), (WIDTH//2, HEIGHT))
    pygame.draw.rect(WIN, (128,128,128), obstacle)
    # Draw split balls if active
    if split_active:
        for b in split_balls:
            pygame.draw.ellipse(WIN, theme["ball"], b["rect"])
    # Crazy mode flash
    if crazy_mode_active:
        pygame.draw.rect(WIN, (255,0,0), (0,0,WIDTH,40))
        crazy_text = FONT.render("CRAZY MODE!", True, (255,255,255))
        WIN.blit(crazy_text, (WIDTH//2 - crazy_text.get_width()//2, 2))
    player_text = FONT.render(f"{player_score}", True, WHITE)
    ai_text = FONT.render(f"{ai_score}", True, WHITE)
    WIN.blit(player_text, (WIDTH//4, 20))
    WIN.blit(ai_text, (WIDTH*3//4, 20))
    draw_powerup()
    # Draw high score
    hs_text = FONT.render(f"High Score: {high_score}", True, (200, 200, 0))
    WIN.blit(hs_text, (WIDTH//2 - hs_text.get_width()//2, HEIGHT-40))
    # Draw achievements
    global achievement_timer, challenge_timer
    if achievement_timer > 0:
        ach_text = FONT.render(achievement_message, True, (0,255,0))
        WIN.blit(ach_text, (WIDTH//2 - ach_text.get_width()//2, HEIGHT//2 - 40))
        achievement_timer -= 1
    # Draw challenge message
    if challenge_timer > 0:
        ch_text = FONT.render(challenge_message, True, (255,128,0))
        WIN.blit(ch_text, (WIDTH//2 - ch_text.get_width()//2, HEIGHT//2 + 40))
        challenge_timer -= 1
    # Power-up banner
    if display_powerup_banner:
        pygame.draw.rect(WIN, (0,128,255), (0,40,WIDTH,40))
        banner_text = FONT.render(powerup_banner_text, True, (255,255,255))
        WIN.blit(banner_text, (WIDTH//2 - banner_text.get_width()//2, 42))
    pygame.display.flip()

def handle_player(keys):
    if keys[pygame.K_UP] and player.top > 0:
        player.y -= PADDLE_SPEED
    if keys[pygame.K_DOWN] and player.bottom < HEIGHT:
        player.y += PADDLE_SPEED

def handle_ai():
    if ai.centery < ball.centery and ai.bottom < HEIGHT:
        ai.y += PADDLE_SPEED - 2
    if ai.centery > ball.centery and ai.top > 0:
        ai.y -= PADDLE_SPEED - 2

# Two-player paddle handler
def handle_player2(keys):
    global TWO_PLAYER
    if keys[pygame.K_w] or keys[pygame.K_s]:
        TWO_PLAYER = True
    if TWO_PLAYER:
        if keys[pygame.K_w] and ai.top > 0:
            ai.y -= PADDLE_SPEED
        if keys[pygame.K_s] and ai.bottom < HEIGHT:
            ai.y += PADDLE_SPEED

def move_ball():
    global BALL_SPEED_X, BALL_SPEED_Y, player_score, ai_score, crazy_mode_active, CRAZY_MODE_TIMER
    # Crazy mode: randomize ball speed/direction
    if not crazy_mode_active and random.random() < CRAZY_MODE_CHANCE:
        crazy_mode_active = True
        CRAZY_MODE_TIMER = CRAZY_MODE_DURATION
        BALL_SPEED_X = random.choice([-1, 1]) * random.randint(4, 10)
        BALL_SPEED_Y = random.choice([-1, 1]) * random.randint(4, 10)
    if crazy_mode_active:
        CRAZY_MODE_TIMER -= 1
        if CRAZY_MODE_TIMER <= 0:
            crazy_mode_active = False
            BALL_SPEED_X = 6 * (1 if BALL_SPEED_X > 0 else -1)
            BALL_SPEED_Y = 6 * (1 if BALL_SPEED_Y > 0 else -1)
    ball.x += BALL_SPEED_X
    ball.y += BALL_SPEED_Y

    # Top/bottom collision
    if ball.top <= 0 or ball.bottom >= HEIGHT:
        BALL_SPEED_Y *= -1
        play_sound(HIT_SOUND)

    # Paddle collision
    if ball.colliderect(player) or ball.colliderect(ai):
        if vector_mode:
            if ball.colliderect(player):
                BALL_SPEED_X = abs(BALL_SPEED_X)
                # Only affect if paddle is moving
                if abs(player_vel) > 0.1:
                    if (BALL_SPEED_Y * player_vel) > 0:
                        # Same direction: increase speed
                        BALL_SPEED_Y += abs(player_vel) * 0.7
                    else:
                        # Opposite direction: decrease speed
                        BALL_SPEED_Y -= abs(player_vel) * 0.7
            else:
                BALL_SPEED_X = -abs(BALL_SPEED_X)
                if abs(ai_vel) > 0.1:
                    if (BALL_SPEED_Y * ai_vel) > 0:
                        BALL_SPEED_Y += abs(ai_vel) * 0.7
                    else:
                        BALL_SPEED_Y -= abs(ai_vel) * 0.7
        else:
            if ball.colliderect(player):
                last_paddle_touched = "player"
            else:
                last_paddle_touched = "ai"
            BALL_SPEED_X, BALL_SPEED_Y = randomize_ball_angle(BALL_SPEED_X, BALL_SPEED_Y, 'x')
        play_sound(HIT_SOUND)

    # Score
    if ball.left <= 0:
        ai_score += 1
        reset_ball()
    if ball.right >= WIDTH:
        player_score += 1
        reset_ball()

    # Move split balls if active
    if split_active:
        for b in split_balls:
            b["rect"].x += b["vx"]
            b["rect"].y += b["vy"]
            # Bounce off top/bottom
            if b["rect"].top <= 0 or b["rect"].bottom >= HEIGHT:
                b["vy"] *= -1
            # Bounce off paddles
            if b["rect"].colliderect(player) or b["rect"].colliderect(ai):
                b["vx"], b["vy"] = randomize_ball_angle(b["vx"], b["vy"], 'x')
            # Score
            if b["rect"].left <= 0:
                ai_score += 1
                b["rect"].center = (WIDTH//2, HEIGHT//2)
            if b["rect"].right >= WIDTH:
                player_score += 1
                b["rect"].center = (WIDTH//2, HEIGHT//2)

# --- SLOW MOTION ---
slowmo = False
slowmo_timer = 0
SLOWMO_DURATION = 10  # frames (was 30)
SLOWMO_FACTOR = 0.3

# --- GAME STATES ---
STATE_TITLE = 0
STATE_PLAY = 1
STATE_FOURP_SETUP = 2
STATE_CHALLENGE_SELECT = 3
STATE_QUIT = 4
game_state = STATE_TITLE
selected_mode = 0  # 0: 1P vs AI, 1: 2P, 2: 4P
selected_fourp = 0  # 0: 1P vs 3CPU, 1: 2P vs 2CPU
challenge_mode = False

# Add challenge select screen
# Add vector_mode flag
vector_mode = False

# Update challenge select screen to include Vector Mode
vector_select_index = 0  # 0: Normal, 1: Challenge, 2: Vector

def draw_challenge_select():
    WIN.fill((20, 20, 40))
    title = FONT.render("Select Mode", True, (255,255,0))
    WIN.blit(title, (WIDTH//2 - title.get_width()//2, 40))
    opts = ["1. Normal", "2. Challenge", "3. Vector"]
    for i, opt in enumerate(opts):
        color = (0,255,0) if i == vector_select_index else (255,255,255)
        opt_text = FONT.render(opt, True, color)
        WIN.blit(opt_text, (WIDTH//2 - opt_text.get_width()//2, 120 + i*50))
    info = pygame.font.SysFont("Arial", 20).render("Use UP/DOWN to select, ENTER to confirm", True, (200,200,200))
    WIN.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT-40))
    pygame.display.flip()

def draw_title():
    WIN.fill((20, 20, 40))
    title = FONT.render("QUICK PONG!", True, (255,255,0))
    WIN.blit(title, (WIDTH//2 - title.get_width()//2, 40))
    opts = ["1. Single Player vs Computer", "2. Two Player", "3. Four Player"]
    for i, opt in enumerate(opts):
        color = (0,255,0) if i == selected_mode else (255,255,255)
        opt_text = FONT.render(opt, True, color)
        WIN.blit(opt_text, (WIDTH//2 - opt_text.get_width()//2, 120 + i*50))
    info = pygame.font.SysFont("Arial", 20).render("Use UP/DOWN to select, ENTER to confirm", True, (200,200,200))
    WIN.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT-40))
    pygame.display.flip()

def draw_fourp_setup():
    WIN.fill((20, 20, 40))
    title = FONT.render("Four Player Mode", True, (255,255,0))
    WIN.blit(title, (WIDTH//2 - title.get_width()//2, 40))
    opts = ["1. 1P vs 3 CPU", "2. 2P vs 2 CPU"]
    for i, opt in enumerate(opts):
        color = (0,255,0) if i == selected_fourp else (255,255,255)
        opt_text = FONT.render(opt, True, color)
        WIN.blit(opt_text, (WIDTH//2 - opt_text.get_width()//2, 120 + i*50))
    info = pygame.font.SysFont("Arial", 20).render("Use UP/DOWN to select, ENTER to confirm", True, (200,200,200))
    WIN.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT-40))
    pygame.display.flip()

# --- FOUR PLAYER MODE VARS ---
four_player_mode = False
fourp_scores = [0, 0, 0, 0]  # [left, right, top, bottom]
# Paddle rects: left, right, top, bottom
paddle_left = player
paddle_right = ai
paddle_top = pygame.Rect(WIDTH//2 - PADDLE_HEIGHT//2, 10, PADDLE_HEIGHT, PADDLE_WIDTH)
paddle_bottom = pygame.Rect(WIDTH//2 - PADDLE_HEIGHT//2, HEIGHT-10-PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_WIDTH)

# Add these variables for four-player paddle allocation:
paddle_assignments = []  # [left, right, top, bottom] - 0=CPU, 1=P1, 2=P2
paddle_labels = ["CPU", "P1", "P2"]

def assign_fourp_paddles(two_player):
    global paddle_assignments
    if two_player:
        # 2P vs 2CPU: randomly assign 2 paddles to players
        available = [0, 1, 2, 3]  # left, right, top, bottom
        p1_paddle = random.choice(available)
        available.remove(p1_paddle)
        p2_paddle = random.choice(available)
        paddle_assignments = [0, 0, 0, 0]  # all CPU initially
        paddle_assignments[p1_paddle] = 1  # P1
        paddle_assignments[p2_paddle] = 2  # P2
    else:
        # 1P vs 3CPU: randomly assign 1 paddle to player
        player_paddle = random.randint(0, 3)
        paddle_assignments = [0, 0, 0, 0]  # all CPU initially
        paddle_assignments[player_paddle] = 1  # P1

def get_paddle_controls(paddle_index):
    # Return the control keys for a given paddle
    if paddle_index == 0:  # left
        return "UP/DOWN"
    elif paddle_index == 1:  # right
        return "W/S"
    elif paddle_index == 2:  # top
        return "A/D"
    elif paddle_index == 3:  # bottom
        return "J/L"

def reset_fourp_ball():
    ball.center = (WIDTH//2, HEIGHT//2)
    ball.x = WIDTH//2 - BALL_SIZE//2
    ball.y = HEIGHT//2 - BALL_SIZE//2
    global BALL_SPEED_X, BALL_SPEED_Y
    BALL_SPEED_X = random.choice([-1, 1]) * random.randint(4, 8)
    BALL_SPEED_Y = random.choice([-1, 1]) * random.randint(4, 8)
    BALL_SPEED_X = max(min(BALL_SPEED_X, MAX_BALL_SPEED), -MAX_BALL_SPEED)
    BALL_SPEED_Y = max(min(BALL_SPEED_Y, MAX_BALL_SPEED), -MAX_BALL_SPEED)

def handle_fourp_controls(keys, two_player):
    # Left paddle (index 0)
    if paddle_assignments[0] == 1:  # P1 controls left
        if keys[pygame.K_UP] and paddle_left.top > 0:
            paddle_left.y -= PADDLE_SPEED
        if keys[pygame.K_DOWN] and paddle_left.bottom < HEIGHT:
            paddle_left.y += PADDLE_SPEED
    elif paddle_assignments[0] == 2:  # P2 controls left
        if keys[pygame.K_w] and paddle_left.top > 0:
            paddle_left.y -= PADDLE_SPEED
        if keys[pygame.K_s] and paddle_left.bottom < HEIGHT:
            paddle_left.y += PADDLE_SPEED
    else:  # CPU controls left
        if paddle_left.centery < ball.centery and paddle_left.bottom < HEIGHT:
            paddle_left.y += PADDLE_SPEED - 2
        if paddle_left.centery > ball.centery and paddle_left.top > 0:
            paddle_left.y -= PADDLE_SPEED - 2
    
    # Right paddle (index 1)
    if paddle_assignments[1] == 1:  # P1 controls right
        if keys[pygame.K_UP] and paddle_right.top > 0:
            paddle_right.y -= PADDLE_SPEED
        if keys[pygame.K_DOWN] and paddle_right.bottom < HEIGHT:
            paddle_right.y += PADDLE_SPEED
    elif paddle_assignments[1] == 2:  # P2 controls right
        if keys[pygame.K_w] and paddle_right.top > 0:
            paddle_right.y -= PADDLE_SPEED
        if keys[pygame.K_s] and paddle_right.bottom < HEIGHT:
            paddle_right.y += PADDLE_SPEED
    else:  # CPU controls right
        if paddle_right.centery < ball.centery and paddle_right.bottom < HEIGHT:
            paddle_right.y += PADDLE_SPEED - 2
        if paddle_right.centery > ball.centery and paddle_right.top > 0:
            paddle_right.y -= PADDLE_SPEED - 2
    
    # Top paddle (index 2)
    if paddle_assignments[2] == 1:  # P1 controls top
        if keys[pygame.K_a] and paddle_top.left > 0:
            paddle_top.x -= PADDLE_SPEED
        if keys[pygame.K_d] and paddle_top.right < WIDTH:
            paddle_top.x += PADDLE_SPEED
    elif paddle_assignments[2] == 2:  # P2 controls top
        if keys[pygame.K_j] and paddle_top.left > 0:
            paddle_top.x -= PADDLE_SPEED
        if keys[pygame.K_l] and paddle_top.right < WIDTH:
            paddle_top.x += PADDLE_SPEED
    else:  # CPU controls top
        if paddle_top.centerx < ball.centerx and paddle_top.right < WIDTH:
            paddle_top.x += PADDLE_SPEED - 2
        if paddle_top.centerx > ball.centerx and paddle_top.left > 0:
            paddle_top.x -= PADDLE_SPEED - 2
    
    # Bottom paddle (index 3)
    if paddle_assignments[3] == 1:  # P1 controls bottom
        if keys[pygame.K_a] and paddle_bottom.left > 0:
            paddle_bottom.x -= PADDLE_SPEED
        if keys[pygame.K_d] and paddle_bottom.right < WIDTH:
            paddle_bottom.x += PADDLE_SPEED
    elif paddle_assignments[3] == 2:  # P2 controls bottom
        if keys[pygame.K_j] and paddle_bottom.left > 0:
            paddle_bottom.x -= PADDLE_SPEED
        if keys[pygame.K_l] and paddle_bottom.right < WIDTH:
            paddle_bottom.x += PADDLE_SPEED
    else:  # CPU controls bottom
        if paddle_bottom.centerx < ball.centerx and paddle_bottom.right < WIDTH:
            paddle_bottom.x += PADDLE_SPEED - 2
        if paddle_bottom.centerx > ball.centerx and paddle_bottom.left > 0:
            paddle_bottom.x -= PADDLE_SPEED - 2

def move_fourp_ball():
    global BALL_SPEED_X, BALL_SPEED_Y, fourp_scores
    ball.x += BALL_SPEED_X
    ball.y += BALL_SPEED_Y
    # Paddle collisions
    if ball.colliderect(paddle_left):
        if vector_mode:
            BALL_SPEED_X = abs(BALL_SPEED_X)
            if abs(paddle_left_vel) > 0.1:
                if (BALL_SPEED_Y * paddle_left_vel) > 0:
                    BALL_SPEED_Y += abs(paddle_left_vel) * 0.7
                else:
                    BALL_SPEED_Y -= abs(paddle_left_vel) * 0.7
        else:
            last_paddle_touched = "left"
            BALL_SPEED_X, BALL_SPEED_Y = randomize_ball_angle(BALL_SPEED_X, BALL_SPEED_Y, 'x')
        play_sound(HIT_SOUND)
    if ball.colliderect(paddle_right):
        if vector_mode:
            BALL_SPEED_X = -abs(BALL_SPEED_X)
            if abs(paddle_right_vel) > 0.1:
                if (BALL_SPEED_Y * paddle_right_vel) > 0:
                    BALL_SPEED_Y += abs(paddle_right_vel) * 0.7
                else:
                    BALL_SPEED_Y -= abs(paddle_right_vel) * 0.7
        else:
            last_paddle_touched = "right"
            BALL_SPEED_X, BALL_SPEED_Y = randomize_ball_angle(BALL_SPEED_X, BALL_SPEED_Y, 'x')
        play_sound(HIT_SOUND)
    if ball.colliderect(paddle_top):
        if vector_mode:
            BALL_SPEED_Y = abs(BALL_SPEED_Y)
            if abs(paddle_top_vel) > 0.1:
                if (BALL_SPEED_X * paddle_top_vel) > 0:
                    BALL_SPEED_X += abs(paddle_top_vel) * 0.7
                else:
                    BALL_SPEED_X -= abs(paddle_top_vel) * 0.7
        else:
            last_paddle_touched = "top"
            BALL_SPEED_X, BALL_SPEED_Y = randomize_ball_angle(BALL_SPEED_X, BALL_SPEED_Y, 'y')
        play_sound(HIT_SOUND)
    if ball.colliderect(paddle_bottom):
        if vector_mode:
            BALL_SPEED_Y = -abs(BALL_SPEED_Y)
            if abs(paddle_bottom_vel) > 0.1:
                if (BALL_SPEED_X * paddle_bottom_vel) > 0:
                    BALL_SPEED_X += abs(paddle_bottom_vel) * 0.7
                else:
                    BALL_SPEED_X -= abs(paddle_bottom_vel) * 0.7
        else:
            last_paddle_touched = "bottom"
            BALL_SPEED_X, BALL_SPEED_Y = randomize_ball_angle(BALL_SPEED_X, BALL_SPEED_Y, 'y')
        play_sound(HIT_SOUND)
    # Wall scoring
    if ball.left <= 0:
        fourp_scores[0] += 1
        reset_fourp_ball()
        play_sound(SCORE_SOUND)
    if ball.right >= WIDTH:
        fourp_scores[1] += 1
        reset_fourp_ball()
        play_sound(SCORE_SOUND)
    if ball.top <= 0:
        fourp_scores[2] += 1
        reset_fourp_ball()
        play_sound(SCORE_SOUND)
    if ball.bottom >= HEIGHT:
        fourp_scores[3] += 1
        reset_fourp_ball()
        play_sound(SCORE_SOUND)

    # Move split balls if active
    if split_active:
        for b in split_balls:
            b["rect"].x += b["vx"]
            b["rect"].y += b["vy"]
            # Bounce off top/bottom
            if b["rect"].top <= 0 or b["rect"].bottom >= HEIGHT:
                b["vy"] *= -1
            # Bounce off paddles
            if b["rect"].colliderect(paddle_left):
                b["vx"], b["vy"] = randomize_ball_angle(b["vx"], b["vy"], 'x')
            if b["rect"].colliderect(paddle_right):
                b["vx"], b["vy"] = randomize_ball_angle(b["vx"], b["vy"], 'x')
            if b["rect"].colliderect(paddle_top):
                b["vx"], b["vy"] = randomize_ball_angle(b["vx"], b["vy"], 'y')
            if b["rect"].colliderect(paddle_bottom):
                b["vx"], b["vy"] = randomize_ball_angle(b["vx"], b["vy"], 'y')
            # Score
            if b["rect"].left <= 0:
                fourp_scores[0] += 1
                b["rect"].center = (WIDTH//2, HEIGHT//2)
            if b["rect"].right >= WIDTH:
                fourp_scores[1] += 1
                b["rect"].center = (WIDTH//2, HEIGHT//2)
            if b["rect"].top <= 0:
                fourp_scores[2] += 1
                b["rect"].center = (WIDTH//2, HEIGHT//2)
            if b["rect"].bottom >= HEIGHT:
                fourp_scores[3] += 1
                b["rect"].center = (WIDTH//2, HEIGHT//2)

def draw_fourp():
    theme = THEMES[current_theme]
    WIN.fill(theme["bg"])
    
    # Draw paddles with labels
    paddles = [paddle_left, paddle_right, paddle_top, paddle_bottom]
    for i, paddle in enumerate(paddles):
        # Draw paddle
        pygame.draw.rect(WIN, theme["paddle"], paddle)
        
        # Draw label
        label = paddle_labels[paddle_assignments[i]]
        label_color = (0,255,0) if paddle_assignments[i] > 0 else (128,128,128)
        font_small = pygame.font.SysFont("Arial", 16)
        label_text = font_small.render(label, True, label_color)
        
        # Position label on paddle
        if i < 2:  # left/right paddles
            label_x = paddle.centerx - label_text.get_width()//2
            label_y = paddle.centery - label_text.get_height()//2
        else:  # top/bottom paddles
            label_x = paddle.centerx - label_text.get_width()//2
            label_y = paddle.centery - label_text.get_height()//2
        
        WIN.blit(label_text, (label_x, label_y))
    
    pygame.draw.ellipse(WIN, theme["ball"], ball)
    
    # Scores
    font_small = pygame.font.SysFont("Arial", 24)
    labels = ["L", "R", "T", "B"]
    for i, score in enumerate(fourp_scores):
        color = (0,255,0) if score == min(fourp_scores) else (255,255,255)
        txt = font_small.render(f"{labels[i]}: {score}", True, color)
        if i == 0:
            WIN.blit(txt, (10, HEIGHT//2 - 30))
        elif i == 1:
            WIN.blit(txt, (WIDTH - txt.get_width() - 10, HEIGHT//2 - 30))
        elif i == 2:
            WIN.blit(txt, (WIDTH//2 - txt.get_width()//2, 10))
        elif i == 3:
            WIN.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT - 30))
    
    # Show controls info
    controls_font = pygame.font.SysFont("Arial", 14)
    controls_text = controls_font.render("P1: UP/DOWN or A/D, P2: W/S or J/L", True, (200,200,200))
    WIN.blit(controls_text, (WIDTH//2 - controls_text.get_width()//2, HEIGHT - 15))
    
    # Draw split balls if active
    if split_active:
        for b in split_balls:
            pygame.draw.ellipse(WIN, theme["ball"], b["rect"])

    # Draw vector mode banner if active
    if vector_mode:
        pygame.draw.rect(WIN, (0,0,0), (0,0,WIDTH,40))
        vector_text = FONT.render("VECTOR MODE", True, (0,255,255))
        WIN.blit(vector_text, (WIDTH//2 - vector_text.get_width()//2, 2))

    pygame.display.flip()

def return_to_title():
    save_high_score()
    global game_state, four_player_mode, player_score, ai_score, fourp_scores, difficulty_level, PADDLE_SPEED, obstacle_speed, PADDLE_HEIGHT
    game_state = STATE_TITLE
    four_player_mode = False
    player_score = 0
    ai_score = 0
    fourp_scores = [0, 0, 0, 0]
    # Reset difficulty
    difficulty_level = 1
    PADDLE_SPEED = 7
    obstacle_speed = 3
    PADDLE_HEIGHT = 100
    # Reset paddle sizes
    player.height = PADDLE_HEIGHT
    ai.height = PADDLE_HEIGHT
    paddle_left.height = PADDLE_HEIGHT
    paddle_right.height = PADDLE_HEIGHT
    paddle_top.width = PADDLE_HEIGHT
    paddle_bottom.width = PADDLE_HEIGHT

# Place these initializations near the top of the file, after imports and before any function definitions:
display_powerup_banner = False
powerup_banner_text = ""
powerup_banner_timer = 0
POWERUP_BANNER_DURATION = 60
split_balls = []
split_active = False
split_timer = 0
SPLIT_DURATION = 600  # 10 seconds at 60 FPS
BALL_SPEED_INCREMENT = 0.2
PADDLE_SPEED_INCREMENT = 0.2
OBSTACLE_SPEED_INCREMENT = 0.2
MAX_BALL_SPEED = 12
MAX_PADDLE_SPEED = 12
MIN_PADDLE_HEIGHT = 30

# Add paddle velocity tracking variables at the top:
player_prev_y = 0
player_vel = 0
ai_prev_y = 0
ai_vel = 0
paddle_left_prev_y = 0
paddle_left_vel = 0
paddle_right_prev_y = 0
paddle_right_vel = 0
paddle_top_prev_x = 0
paddle_top_vel = 0
paddle_bottom_prev_x = 0
paddle_bottom_vel = 0

# --- WINDOWS OVERLAY MODE ---
# Add global variable for overlay alpha
overlay_alpha = 0.3

# Update set_windows_overlay to use overlay_alpha

def set_windows_overlay(alpha=None):
    if sys.platform != "win32":
        return
    import ctypes
    hwnd = pygame.display.get_wm_info()["window"]
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x80000
    WS_EX_TOPMOST = 0x0008
    WS_EX_TOOLWINDOW = 0x00000080
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style |= WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    LWA_ALPHA = 0x2
    a = int((alpha if alpha is not None else overlay_alpha) * 255)
    ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, a, LWA_ALPHA)
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)

# --- OVERLAY MODE FLAG ---
# Set overlay_mode default to True
overlay_mode = True  # Overlay mode enabled by default

# Add this near the top of the file, before main():
show_controls = False

def draw_controls_screen():
    WIN.fill((20, 20, 40))
    title = FONT.render("Controls", True, (255,255,0))
    WIN.blit(title, (WIDTH//2 - title.get_width()//2, 40))
    lines = [
        "ESC: Return to Title Screen",
        "F1: Show/Hide Controls",
        "M: More Transparent (Overlay Mode)",
        "N: Less Transparent (Overlay Mode)",
        "C: Change Color Theme",
        "Up/Down: Move Paddle (P1)",
        "W/S: Move Paddle (P2 or AI)",
        "A/D: Move Top Paddle (P1 or P2)",
        "J/L: Move Bottom Paddle (P2 or P1)",
        "Space/Enter: Dismiss Controls"
    ]
    for i, line in enumerate(lines):
        txt = pygame.font.SysFont("Arial", 24).render(line, True, (255,255,255))
        WIN.blit(txt, (WIDTH//2 - txt.get_width()//2, 120 + i*35))
    pygame.display.flip()

def main():
    global WIDTH, HEIGHT, WIN, overlay_mode
    global slowmo, slowmo_timer, game_state, selected_mode, selected_fourp, TWO_PLAYER, four_player_mode, fourp_scores, challenge_mode, display_powerup_banner, powerup_banner_text, powerup_banner_timer, split_active, split_balls, split_timer, vector_mode, vector_select_index, player_prev_y, player_vel, ai_prev_y, ai_vel, paddle_left_prev_y, paddle_left_vel, paddle_right_prev_y, paddle_right_vel, paddle_top_prev_x, paddle_top_vel, paddle_bottom_prev_x, paddle_bottom_vel, overlay_alpha, show_controls, clock
    clock = pygame.time.Clock()
    running = True
    load_high_score()
    # After pygame.init(), set overlay mode ON by default
    if overlay_mode:
        info = pygame.display.Info()
        WIDTH, HEIGHT = info.current_w, info.current_h
        WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
        set_windows_overlay(overlay_alpha)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if game_state == STATE_TITLE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_mode = (selected_mode - 1) % 3
                    if event.key == pygame.K_DOWN:
                        selected_mode = (selected_mode + 1) % 3
                    if event.key == pygame.K_RETURN:
                        if selected_mode == 2:
                            game_state = STATE_FOURP_SETUP
                        else:
                            game_state = STATE_CHALLENGE_SELECT
            elif game_state == STATE_FOURP_SETUP:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                        selected_fourp = (selected_fourp + 1) % 2
                    if event.key == pygame.K_RETURN:
                        game_state = STATE_CHALLENGE_SELECT
            elif game_state == STATE_CHALLENGE_SELECT:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        vector_select_index = (vector_select_index - 1) % 3
                    if event.key == pygame.K_DOWN:
                        vector_select_index = (vector_select_index + 1) % 3
                    if event.key == pygame.K_RETURN:
                        game_state = STATE_PLAY
                        TWO_PLAYER = (selected_mode == 1)
                        four_player_mode = (selected_mode == 2)
                        fourp_scores[:] = [0,0,0,0]
                        challenge_mode = (vector_select_index == 1)
                        vector_mode = (vector_select_index == 2)
                        if four_player_mode:
                            assign_fourp_paddles(selected_fourp == 1)
                        # Optionally set up which paddles are human/AI based on selected_fourp
            elif game_state == STATE_PLAY:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:
                        global current_theme
                        current_theme = (current_theme + 1) % len(THEMES)
                    if event.key == pygame.K_ESCAPE:
                        return_to_title()
                    if event.key == pygame.K_F1:
                        show_controls = not show_controls
                    if show_controls and (event.key == pygame.K_SPACE or event.key == pygame.K_RETURN):
                        show_controls = False
                    if overlay_mode:
                        if event.key == pygame.K_q:
                            pygame.quit()
                            sys.exit()
                        if event.key == pygame.K_m:
                            overlay_alpha = min(0.5, overlay_alpha + 0.02)
                            if overlay_mode:
                                set_windows_overlay(overlay_alpha)
                        if event.key == pygame.K_n:
                            overlay_alpha = max(0.02, overlay_alpha - 0.02)
                            if overlay_mode:
                                set_windows_overlay(overlay_alpha)
                        if event.key == pygame.K_o:
                            overlay_mode = not overlay_mode
                            if overlay_mode:
                                info = pygame.display.Info()
                                WIDTH, HEIGHT = info.current_w, info.current_h
                                WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
                                set_windows_overlay(overlay_alpha)
                            else:
                                WIN = pygame.display.set_mode((WIDTH, HEIGHT))
        if game_state == STATE_TITLE:
            draw_title()
            clock.tick(30)
            continue
        if game_state == STATE_FOURP_SETUP:
            draw_fourp_setup()
            clock.tick(30)
            continue
        if game_state == STATE_CHALLENGE_SELECT:
            draw_challenge_select()
            clock.tick(30)
            continue
        keys = pygame.key.get_pressed()
        if four_player_mode:
            handle_fourp_controls(keys, selected_fourp == 1)
            move_fourp_ball()
            draw_fourp()
            clock.tick(60)
            continue
        # Track paddle velocities for vector mode
        if vector_mode:
            player_vel = player.y - player_prev_y
            player_prev_y = player.y
            ai_vel = ai.y - ai_prev_y
            ai_prev_y = ai.y
            paddle_left_vel = paddle_left.y - paddle_left_prev_y
            paddle_left_prev_y = paddle_left.y
            paddle_right_vel = paddle_right.y - paddle_right_prev_y
            paddle_right_prev_y = paddle_right.y
            paddle_top_vel = paddle_top.x - paddle_top_prev_x
            paddle_top_prev_x = paddle_top.x
            paddle_bottom_vel = paddle_bottom.x - paddle_bottom_prev_x
            paddle_bottom_prev_x = paddle_bottom.x

        handle_player(keys)
        handle_player2(keys)
        if not TWO_PLAYER:
            handle_ai()
        move_ball()
        move_obstacle()
        handle_obstacle_collision()
        spawn_powerup()
        handle_powerup_collision()
        update_powerup()
        # SLOW MOTION: if ball is near edge, slow down
        if not slowmo and (ball.left < 30 or ball.right > WIDTH-30):
            slowmo = True
            slowmo_timer = SLOWMO_DURATION
        # Prevent retriggering slowmo while already active
        if slowmo and (ball.left < 30 or ball.right > WIDTH-30) and slowmo_timer < SLOWMO_DURATION:
            pass  # Do not retrigger or extend slowmo
        if slowmo:
            clock.tick(int(60 * SLOWMO_FACTOR))
            slowmo_timer -= 1
            if slowmo_timer <= 0:
                slowmo = False
        else:
            clock.tick(60)
        draw()
        if show_controls:
            draw_controls_screen()
            clock.tick(30)
            continue
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main() 