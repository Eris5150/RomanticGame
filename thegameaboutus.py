import pygame
import random
import math
import sys, os
from pygame import mixer

# ==============================================================
# 💘 MEMORY INVADERS
# --------------------------------------------------------------
# A romantic twist on the classic Space Invaders built with Pygame.
# Use your mouse to move Cupid’s bow and shoot hearts to stop
# waves of teddy bears before they reach you.
# ==============================================================


# -------- Resource Path Helper (works in .py and .exe) --------
def resource_path(relative_path: str) -> str:
    """
    Returns an absolute path valid both when running the script normally
    and when bundled with PyInstaller (which uses the _MEIPASS folder).
    This ensures all assets (images, sounds) load correctly.
    """
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# -------- Initialization --------
pygame.init()
mixer.init()  # Recommended to initialize mixer early to avoid sound lag


# -------- Screen Setup --------
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Invaders")
icon = pygame.image.load(resource_path("love-always-wins.png"))
pygame.display.set_icon(icon)


# -------- Fonts --------
font = pygame.font.SysFont("Arial", 28, bold=True)
big_font = pygame.font.SysFont("Arial", 44, bold=True)


# -------- Colors --------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PINK = (255, 153, 204)
RED = (255, 102, 102)
GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)


# -------- Background Music --------
mixer.music.load(resource_path("MusicaFondo.mp3"))
mixer.music.set_volume(0.3)
mixer.music.play(-1)  # -1 makes it loop indefinitely


# -------- Load Images --------
player_img = pygame.transform.rotate(
    pygame.transform.scale(
        pygame.image.load(resource_path("love-archery.png")), (64, 64)
    ),
    90,  # Rotate the bow 90° so it faces upward
)
bullet_img = pygame.transform.scale(
    pygame.image.load(resource_path("cupid.png")), (20, 30)
)
enemy_img_base = pygame.transform.scale(
    pygame.image.load(resource_path("teddy-bear.png")), (64, 64)
)
heart_img = pygame.transform.scale(
    pygame.image.load(resource_path("heart.png")), (20, 20)
)


# -------- Entity Settings --------
player_width, player_height = 64, 64
bullet_speed = 6
enemy_speed = 0.8
enemy_y_base_change = 50
num_enemies = 20  # Number of teddy bears on screen


# -------- Bullets / Cooldown --------
bullets = []
last_shot_time = 0
shot_cooldown = 0.5  # Intended cooldown (milliseconds)


# -------- Game State Initialization --------
def reset_game():
    """
    Resets all positions, scores, enemies, and states.
    Called when the player starts or restarts a game.
    """
    global player_x, player_y, bullets, score
    global enemy_x, enemy_y, enemy_x_change, enemy_y_change
    global game_over, game_won, explosions, last_shot_time

    player_x = WIDTH // 2
    player_y = HEIGHT - 80
    bullets = []
    score = 0
    explosions = []
    enemy_x = [random.randint(0, WIDTH - 64) for _ in range(num_enemies)]
    enemy_y = [random.randint(50, 150) for _ in range(num_enemies)]
    enemy_x_change = [enemy_speed for _ in range(num_enemies)]
    enemy_y_change = [enemy_y_base_change for _ in range(num_enemies)]
    last_shot_time = 0
    game_over = False
    game_won = False


reset_game()  # Initialize first game session


# -------- Utility: Draw Text --------
def draw_text(text, x, y, size=28, color=BLACK, center=False):
    """
    Draws text with a subtle shadow for readability.
    """
    t_font = pygame.font.SysFont("Arial", size, bold=True)
    shadow = t_font.render(text, True, DARK_GRAY)
    label = t_font.render(text, True, color)
    if center:
        rect = label.get_rect(center=(x, y))
        screen.blit(shadow, (rect.x + 2, rect.y + 2))
        screen.blit(label, rect)
    else:
        screen.blit(shadow, (x + 2, y + 2))
        screen.blit(label, (x, y))


# -------- Utility: Draw Button --------
def draw_button(text, x, y, w, h, action=None):
    """
    Draws a clickable rounded button.
    When hovered, it changes color and executes `action()` on click.
    """
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    hovered = x < mouse[0] < x + w and y < mouse[1] < y + h

    color = RED if hovered else GRAY
    pygame.draw.rect(screen, color, (x, y, w, h), border_radius=10)
    draw_text(text, x + w // 2, y + h // 2, size=28, color=WHITE, center=True)

    # Detect button click
    if hovered and click[0] and action:
        pygame.time.delay(200)
        action()


# -------- Preload Sounds --------
snd_disparo = mixer.Sound(resource_path("disparo.mp3"))
snd_golpe = mixer.Sound(resource_path("golpe.mp3"))


# -------- Fire Bullet --------
def fire_bullet():
    """
    Creates and launches a bullet if enough time has passed since the last shot.
    """
    global last_shot_time
    current_time = pygame.time.get_ticks()
    if current_time - last_shot_time >= shot_cooldown:
        bullet_x = player_x + 22
        bullet_y = player_y
        bullets.append([bullet_x, bullet_y])
        last_shot_time = current_time
        snd_disparo.play()


# -------- Spawn Heart Explosion --------
def spawn_heart_explosion(x, y):
    """
    Creates a heart particle explosion effect at (x, y)
    when an enemy is destroyed.
    """
    group = []
    for _ in range(8):
        dx = random.uniform(-3, 3)
        dy = random.uniform(-3, 3)
        group.append([x, y, dx, dy, 20])  # x, y, velocityX, velocityY, lifespan
    explosions.append(group)


# -------- Collision Detection --------
def is_collision(x1, y1, x2, y2, threshold=50):
    """
    Simple bounding-box collision using absolute distance.
    """
    return abs(x1 - x2) < threshold and abs(y1 - y2) < threshold


# -------- Main Game Loop --------
clock = pygame.time.Clock()
running = True

while running:
    screen.fill(WHITE)

    # -------- Event Handling --------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False  # Close the window

        if not game_over and not game_won:
            # Mouse movement: controls Cupid’s bow
            if event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                player_x = mouse_x - player_width // 2
                player_y = mouse_y - player_height // 2

            # Shooting: spacebar or left click
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or \
               (event.type == pygame.MOUSEBUTTONDOWN):
                fire_bullet()

    # -------- Main Gameplay --------
    if not game_over and not game_won:
        # Keep player inside window boundaries
        player_x = max(0, min(player_x, WIDTH - player_width))
        player_y = max(0, min(player_y, HEIGHT - player_height))

        # --- Enemies ---
        for i in range(num_enemies):
            enemy_x[i] += enemy_x_change[i]
            enemy_y[i] += 0.6 + (score * 0.03)  # Increases difficulty as you score

            # Bounce off edges and descend
            if enemy_x[i] <= 0 or enemy_x[i] >= WIDTH - 64:
                enemy_x_change[i] *= -1
                enemy_y[i] += enemy_y_change[i]

            # Collision with bullets
            for bullet in bullets[:]:
                if is_collision(enemy_x[i], enemy_y[i], bullet[0], bullet[1]):
                    snd_golpe.play()
                    spawn_heart_explosion(enemy_x[i] + 16, enemy_y[i] + 16)
                    bullets.remove(bullet)
                    score += 1
                    # Respawn enemy at random position
                    enemy_x[i] = random.randint(0, WIDTH - 64)
                    enemy_y[i] = random.randint(50, 150)
                    break

            # If enemy touches player or reaches bottom — game over
            if is_collision(enemy_x[i], enemy_y[i], player_x, player_y, 55) or enemy_y[i] >= HEIGHT - 60:
                game_over = True

            screen.blit(enemy_img_base, (enemy_x[i], enemy_y[i]))

        # --- Bullets ---
        for bullet in bullets[:]:
            bullet[1] -= bullet_speed
            screen.blit(bullet_img, (bullet[0], bullet[1]))
            if bullet[1] <= 0:
                bullets.remove(bullet)

        # --- Explosions ---
        for group in explosions:
            for p in group:
                p[0] += p[2]
                p[1] += p[3]
                p[4] -= 1
                screen.blit(heart_img, (p[0], p[1]))
        explosions = [[p for p in g if p[4] > 0] for g in explosions if g]

        # Draw player and HUD
        screen.blit(player_img, (player_x, player_y))
        draw_text(f"Score: {score}", 20, 20)

        # Win condition
        if score >= 15:
            game_won = True

    # -------- Game Over Screen --------
    elif game_over:
        draw_text("GAME OVER", WIDTH // 2, HEIGHT // 2 - 80, size=48, color=RED, center=True)
        draw_button("RESTART", WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 60, action=reset_game)

    # -------- Win Screen --------
    elif game_won:
        draw_text("You did it, mi amor 💖", WIDTH // 2, HEIGHT // 2 - 100, size=40, color=PINK, center=True)
        draw_text("The next clue is in the Friends book", WIDTH // 2, HEIGHT // 2 - 40, size=32, color=BLACK, center=True)
        draw_text("Page 43, Paragraph 2, Word 1", WIDTH // 2, HEIGHT // 2, size=32, color=BLACK, center=True)
        draw_button("RESTART", WIDTH // 2 - 100, WIDTH // 2 + 80, 200, 60, action=reset_game)

    # -------- Frame Update --------
    pygame.display.update()
    clock.tick(60)  # Limit FPS to 60 for smoother performance
