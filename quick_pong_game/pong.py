import pygame
import sys
import random

# Initialize Pygame
pygame.init()

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

def reset_ball():
    global BALL_SPEED_X, BALL_SPEED_Y
    ball.center = (WIDTH//2, HEIGHT//2)
    BALL_SPEED_X = 6 * random.choice((1, -1))
    BALL_SPEED_Y = 6 * random.choice((1, -1))

def draw():
    WIN.fill(BLACK)
    pygame.draw.rect(WIN, WHITE, player)
    pygame.draw.rect(WIN, WHITE, ai)
    pygame.draw.ellipse(WIN, WHITE, ball)
    pygame.draw.aaline(WIN, WHITE, (WIDTH//2, 0), (WIDTH//2, HEIGHT))
    player_text = FONT.render(f"{player_score}", True, WHITE)
    ai_text = FONT.render(f"{ai_score}", True, WHITE)
    WIN.blit(player_text, (WIDTH//4, 20))
    WIN.blit(ai_text, (WIDTH*3//4, 20))
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

def move_ball():
    global BALL_SPEED_X, BALL_SPEED_Y, player_score, ai_score
    ball.x += BALL_SPEED_X
    ball.y += BALL_SPEED_Y

    # Top/bottom collision
    if ball.top <= 0 or ball.bottom >= HEIGHT:
        BALL_SPEED_Y *= -1

    # Paddle collision
    if ball.colliderect(player) or ball.colliderect(ai):
        BALL_SPEED_X *= -1

    # Score
    if ball.left <= 0:
        ai_score += 1
        reset_ball()
    if ball.right >= WIDTH:
        player_score += 1
        reset_ball()

def main():
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        keys = pygame.key.get_pressed()
        handle_player(keys)
        handle_ai()
        move_ball()
        draw()
        clock.tick(60)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main() 