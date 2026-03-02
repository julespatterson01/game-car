import pygame
import sys
from pytmx.util_pygame import load_pygame
from pytmx.pytmx import TiledTileLayer

# -----------------------------
# CONFIG
# -----------------------------
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 400
TILE_SIZE = 32

CAR_WIDTH = 180
CAR_HEIGHT = 100
ACCELERATION = 0.4
BRAKE_FORCE = 1.0
FRICTION = 0.05
MAX_SPEED = 6
GRAVITY = 0.6
TERMINAL_VELOCITY = 12

# -----------------------------
# CAR CLASS
# -----------------------------
class Car:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.rect = pygame.Rect(self.x, self.y, CAR_WIDTH, CAR_HEIGHT)
        self.image = pygame.image.load("realcar1.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (CAR_WIDTH, CAR_HEIGHT))

    def update(self, keys, floor_tiles, ceiling_tiles):
        # Horizontal movement
        if keys[pygame.K_RIGHT]:
            self.vx += ACCELERATION
        elif keys[pygame.K_LEFT]:
            self.vx -= ACCELERATION

        # Braking
        if keys[pygame.K_DOWN]:
            if self.vx > 0:
                self.vx -= BRAKE_FORCE
            elif self.vx < 0:
                self.vx += BRAKE_FORCE

        # Friction
        if not (keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]):
            if self.vx > 0:
                self.vx -= FRICTION
            elif self.vx < 0:
                self.vx += FRICTION

        # Clamp horizontal speed
        self.vx = max(-MAX_SPEED, min(MAX_SPEED, self.vx))
        if abs(self.vx) < 0.1:
            self.vx = 0

        # Apply horizontal movement
        self.x += self.vx
        self.rect.x = self.x

        # Apply gravity
        self.vy += GRAVITY
        if self.vy > TERMINAL_VELOCITY:
            self.vy = TERMINAL_VELOCITY
        self.y += self.vy
        self.rect.y = self.y

        # ----- FLOOR COLLISION -----
        # Find tiles overlapping horizontally
        overlapping_tiles = [tile for tile in floor_tiles if tile.right > self.rect.left and tile.left < self.rect.right]
        if overlapping_tiles:
            # Determine the highest tile the car is standing on
            ground_y = max(tile.top for tile in overlapping_tiles if tile.top <= self.rect.bottom + 50)
            if self.rect.bottom > ground_y:
                self.rect.bottom = ground_y
                self.y = self.rect.y
                self.vy = 0

        # ----- CEILING COLLISION -----
        overlapping_ceiling = [tile for tile in ceiling_tiles if tile.right > self.rect.left and tile.left < self.rect.right]
        if overlapping_ceiling:
            ceiling_y = min(tile.bottom for tile in overlapping_ceiling if tile.bottom >= self.rect.top - 50)
            if self.rect.top < ceiling_y:
                self.rect.top = ceiling_y
                self.y = self.rect.y
                self.vy = 0

    def draw(self, screen, camera_x):
        screen.blit(self.image, (self.rect.x - camera_x, self.rect.y))

# -----------------------------
# INIT PYGAME
# -----------------------------
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2D Car Game")
clock = pygame.time.Clock()

# -----------------------------
# LOAD BACKGROUND
# -----------------------------
background_image = pygame.image.load("background1.png").convert()
background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# -----------------------------
# LOAD TMX MAP
# -----------------------------
tmx_data = load_pygame("Collision1.tmx")
map_width = tmx_data.width * TILE_SIZE
map_height = tmx_data.height * TILE_SIZE

# -----------------------------
# ZERO PADDING: map exactly at bottom
# -----------------------------
MAP_Y_OFFSET = SCREEN_HEIGHT - map_height

# -----------------------------
# FLOOR AND CEILING TILES
# -----------------------------
floor_tiles = []
ceiling_tiles = []

for layer in tmx_data.visible_layers:
    if isinstance(layer, TiledTileLayer):
        for x, y, image in layer.tiles():
            if image:
                rect = pygame.Rect(
                    x * TILE_SIZE,
                    y * TILE_SIZE + MAP_Y_OFFSET,
                    TILE_SIZE,
                    TILE_SIZE
                )
                if layer.name.lower() == "floor":
                    floor_tiles.append(rect)
                elif layer.name.lower() == "ceiling":
                    ceiling_tiles.append(rect)

# -----------------------------
# CREATE CAR INSTANCE ON TRACK
# -----------------------------
car_start_x = 100
# Find all floor tiles under the car's middle point
possible_starts = [tile.top for tile in floor_tiles if tile.left <= car_start_x + CAR_WIDTH // 2 <= tile.right]
car_start_y = min(possible_starts) - CAR_HEIGHT if possible_starts else SCREEN_HEIGHT - CAR_HEIGHT
car = Car(car_start_x, car_start_y)

# -----------------------------
# MAIN LOOP
# -----------------------------
running = True
while running:
    dt = clock.tick(60)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Update car
    car.update(keys, floor_tiles, ceiling_tiles)

    # Camera follows car
    camera_x = max(0, min(car.x - SCREEN_WIDTH // 2, map_width - SCREEN_WIDTH))

    # Draw background
    screen.blit(background_image, (0, 0))

    # Draw tiles
    for layer in tmx_data.visible_layers:
        if isinstance(layer, TiledTileLayer):
            for x, y, image in layer.tiles():
                if image:
                    screen.blit(image, (x * TILE_SIZE - camera_x, y * TILE_SIZE + MAP_Y_OFFSET))

    # Draw car
    car.draw(screen, camera_x)

    pygame.display.update()
