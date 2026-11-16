
import pygame
import random
import sys
import math
import struct

# ============================================================
# ANKRAH SNAKE - ADVANCED SOUND EDITION
# ============================================================

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()

WIDTH, HEIGHT = 700, 740
CELL = 20
LEFT, TOP = 50, 80
COLS, ROWS = 30, 30

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("ANKRAH SNAKE - ADVANCED SOUND EDITION")
clock = pygame.time.Clock()

# COLORS
BLACK = (4, 5, 24)
WHITE = (255, 255, 255)
GREEN = (45, 255, 20)
DARK_GREEN = (10, 130, 10)
PINK = (255, 0, 200)
BLUE = (0, 210, 255)
PURPLE = (190, 0, 255)
RED = (255, 60, 70)
GOLD = (255, 200, 0)

# FONTS
font = pygame.font.SysFont("Arial", 25, bold=True)
small_font = pygame.font.SysFont("Arial", 18)
big_font = pygame.font.SysFont("Arial", 48, bold=True)

# GAME SETTINGS
level = 1
speed = 10
selected = 0
high_score = 0
state = "MENU"
paused = False

snake = []
food = None
obstacles = []
score = 0

direction = (CELL, 0)
next_direction = (CELL, 0)

# AUDIO SETTINGS
sound_enabled = True
volume = 0.45
music_channel = None
sound_channel = None
audio_available = True

try:
    music_channel = pygame.mixer.Channel(0)
    sound_channel = pygame.mixer.Channel(1)
except pygame.error:
    audio_available = False


# ============================================================
# SOUND GENERATOR
# ============================================================

def make_tone(frequency, duration, volume_level=0.35,
              wave_type="sine"):

    if not audio_available:
        return None

    sample_rate = 22050
    count = int(sample_rate * duration)
    samples = bytearray()

    for i in range(count):

        t = i / sample_rate

        fade_in = min(1.0, i / max(1, int(sample_rate * 0.008)))
        fade_out = min(1.0, (count - i) /
                       max(1, int(sample_rate * 0.035)))

        envelope = fade_in * fade_out

        if wave_type == "square":
            wave = 1.0 if math.sin(
                2 * math.pi * frequency * t
            ) >= 0 else -1.0

        elif wave_type == "triangle":
            wave = (2 / math.pi) * math.asin(
                math.sin(2 * math.pi * frequency * t)
            )

        else:
            wave = math.sin(2 * math.pi * frequency * t)

        value = int(32767 * volume_level * envelope * wave)

        samples.extend(
            struct.pack("<h", max(-32767, min(32767, value)))
        )

    try:
        return pygame.mixer.Sound(buffer=bytes(samples))
    except pygame.error:
        return None


def make_music():

    if not audio_available:
        return None

    sample_rate = 22050
    bpm = 112
    beat = 60 / bpm

    notes = [
        (659.25, 0.5), (783.99, 0.5),
        (987.77, 1.0), (783.99, 0.5),
        (659.25, 0.5), (587.33, 1.0),
        (523.25, 0.5), (587.33, 0.5),
        (659.25, 1.0), (783.99, 1.0),
        (698.46, 0.5), (659.25, 0.5),
        (587.33, 1.0), (523.25, 1.0)
    ]

    samples = bytearray()

    for frequency, beats in notes:

        duration = beat * beats
        count = int(sample_rate * duration)

        for i in range(count):

            t = i / sample_rate

            wave = 0.72 * math.sin(
                2 * math.pi * frequency * t
            )

            wave += 0.18 * math.sin(
                2 * math.pi * frequency * 2 * t
            )

            envelope = min(1.0, i / 180) * min(
                1.0, (count - i) / 500
            )

            value = int(32767 * 0.12 * envelope * wave)

            samples.extend(
                struct.pack("<h", max(-32767, min(32767, value)))
            )

    try:
        return pygame.mixer.Sound(buffer=bytes(samples))
    except pygame.error:
        return None


# CREATE SOUNDS
eat_sound = make_tone(880, 0.11, 0.45, "triangle")
level_sound = make_tone(1046.5, 0.30, 0.45, "square")
crash_sound = make_tone(130, 0.55, 0.55, "triangle")
pause_sound = make_tone(520, 0.10, 0.30)
menu_sound = make_tone(660, 0.07, 0.25)

music_sound = make_music()


def play_sound(sound):

    if sound_enabled and audio_available and sound is not None:

        try:
            sound_channel.set_volume(volume)
            sound_channel.play(sound)

        except pygame.error:
            pass


def start_music():

    if sound_enabled and audio_available and music_sound is not None:

        try:
            music_channel.set_volume(volume * 0.55)

            if not music_channel.get_busy():
                music_channel.play(music_sound, loops=-1)

        except pygame.error:
            pass


def stop_music():

    if audio_available and music_channel is not None:
        music_channel.stop()


def toggle_sound():

    global sound_enabled

    sound_enabled = not sound_enabled

    if sound_enabled:
        start_music()
        play_sound(menu_sound)

    else:
        stop_music()

        if sound_channel:
            sound_channel.stop()


# ============================================================
# TEXT DISPLAY
# ============================================================

def draw_text(text, font_style, color, x, y):

    image = font_style.render(text, True, color)
    screen.blit(image, (x, y))


# ============================================================
# BACKGROUND
# ============================================================

def draw_background():

    screen.fill(BLACK)

    pygame.draw.rect(
        screen, PURPLE, (35, 65, 630, 630), 4
    )

    pygame.draw.rect(
        screen, BLUE, (45, 75, 610, 610), 3
    )

    for x in range(LEFT, LEFT + 600, CELL):

        pygame.draw.line(
            screen, (15, 20, 50),
            (x, TOP), (x, TOP + 600)
        )

    for y in range(TOP, TOP + 600, CELL):

        pygame.draw.line(
            screen, (15, 20, 50),
            (LEFT, y), (LEFT + 600, y)
        )


# ============================================================
# SNAKE
# ============================================================

def draw_snake():

    for index, segment in enumerate(snake):

        rect = pygame.Rect(
            segment[0] + 1,
            segment[1] + 1,
            CELL - 2,
            CELL - 2
        )

        color = GREEN if index == 0 else DARK_GREEN

        pygame.draw.rect(
            screen, color, rect, border_radius=5
        )

        pygame.draw.rect(
            screen, GREEN, rect, 1, border_radius=5
        )

        if index == 0:

            if direction == (CELL, 0):
                eyes = [
                    (segment[0] + 14, segment[1] + 6),
                    (segment[0] + 14, segment[1] + 14)
                ]

            elif direction == (-CELL, 0):
                eyes = [
                    (segment[0] + 5, segment[1] + 6),
                    (segment[0] + 5, segment[1] + 14)
                ]

            elif direction == (0, -CELL):
                eyes = [
                    (segment[0] + 6, segment[1] + 5),
                    (segment[0] + 14, segment[1] + 5)
                ]

            else:
                eyes = [
                    (segment[0] + 6, segment[1] + 14),
                    (segment[0] + 14, segment[1] + 14)
                ]

            for eye in eyes:
                pygame.draw.circle(screen, BLACK, eye, 2)


# ============================================================
# FOOD
# ============================================================

def create_food():

    available = [
        (LEFT + col * CELL, TOP + row * CELL)
        for col in range(COLS)
        for row in range(ROWS)
    ]

    unavailable = set(snake) | set(obstacles)

    available = [
        position for position in available
        if position not in unavailable
    ]

    return random.choice(available) if available else None


def draw_food():

    if food is None:
        return

    pygame.draw.circle(
        screen, PINK,
        (food[0] + 10, food[1] + 10), 9
    )

    pygame.draw.circle(
        screen, BLUE,
        (food[0] + 15, food[1] + 5), 4
    )


# ============================================================
# OBSTACLES
# ============================================================

def create_obstacles():

    blocks = []
    amount = (level - 1) * 2

    while len(blocks) < amount:

        col = random.randrange(COLS)
        row = random.randrange(ROWS)

        position = (
            LEFT + col * CELL,
            TOP + row * CELL
        )

        if (
            position not in snake
            and position not in blocks
            and (
                abs(position[0] - 350) > 80
                or abs(position[1] - 380) > 80
            )
        ):

            blocks.append(position)

    return blocks


def draw_obstacles():

    for block in obstacles:

        rect = pygame.Rect(
            block[0] + 1,
            block[1] + 1,
            CELL - 2,
            CELL - 2
        )

        pygame.draw.rect(
            screen, RED, rect, border_radius=4
        )


# ============================================================
# START GAME
# ============================================================

def start_game():

    global snake, food, obstacles
    global score, direction, next_direction
    global paused, state

    snake = [
        (350, 380),
        (330, 380),
        (310, 380)
    ]

    direction = (CELL, 0)
    next_direction = direction

    score = 0
    paused = False

    obstacles = create_obstacles()
    food = create_food()

    state = "PLAYING"

    start_music()


# ============================================================
# MAIN MENU
# ============================================================

def draw_menu():

    screen.fill(BLACK)

    pygame.draw.rect(
        screen, PURPLE, (35, 40, 630, 650), 4
    )

    pygame.draw.rect(
        screen, BLUE, (45, 50, 610, 630), 2
    )

    draw_text(
        "ANKRAH SNAKE",
        big_font, GREEN, 165, 95
    )

    draw_text(
        "ADVANCED SOUND EDITION",
        font, BLUE, 175, 155
    )

    options = [
        f"DIFFICULTY LEVEL: {level}/10",
        f"SNAKE SPEED: {speed}",
        f"SOUND: {'ON' if sound_enabled else 'OFF'}",
        "START GAME"
    ]

    for index, option in enumerate(options):

        y = 255 + index * 65

        color = PINK if selected == index else WHITE

        if selected == index:
            draw_text(">", font, GREEN, 135, y)

        draw_text(option, font, color, 180, y)

    draw_text(
        "UP / DOWN: SELECT",
        small_font, BLUE, 220, 535
    )

    draw_text(
        "LEFT / RIGHT: CHANGE SETTINGS",
        small_font, BLUE, 145, 565
    )

    draw_text(
        "ENTER: START / TOGGLE SOUND",
        small_font, GREEN, 175, 595
    )

    draw_text(
        f"BEST SCORE: {high_score}",
        small_font, GOLD, 240, 645
    )


# ============================================================
# GAME SCREEN
# ============================================================

def draw_game():

    draw_background()

    draw_obstacles()
    draw_snake()
    draw_food()

    draw_text(
        f"SCORE: {score}",
        font, WHITE, 65, 20
    )

    draw_text(
        f"LEVEL: {level}",
        font, GREEN, 275, 20
    )

    draw_text(
        f"SPEED: {speed}",
        font, BLUE, 510, 20
    )

    draw_text(
        f"SOUND: {'ON' if sound_enabled else 'OFF'} (M)",
        small_font, GOLD, 260, 710
    )

    if paused:

        overlay = pygame.Surface(
            (WIDTH, HEIGHT), pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        draw_text(
            "GAME PAUSED",
            big_font, PINK, 205, 320
        )

        draw_text(
            "PRESS P OR SPACE TO RESUME",
            font, WHITE, 145, 390
        )

        draw_text(
            "ESC: MAIN MENU",
            small_font, BLUE, 245, 440
        )


# ============================================================
# GAME OVER
# ============================================================

def draw_game_over():

    screen.fill(BLACK)

    pygame.draw.rect(
        screen, PURPLE, (40, 70, 620, 600), 4
    )

    draw_text(
        "GAME OVER",
        big_font, PINK, 185, 200
    )

    draw_text(
        f"FINAL SCORE: {score}",
        font, WHITE, 220, 290
    )

    draw_text(
        f"BEST SCORE: {high_score}",
        font, GREEN, 220, 340
    )

    draw_text(
        "R - PLAY AGAIN",
        font, BLUE, 235, 430
    )

    draw_text(
        "M - MAIN MENU",
        font, WHITE, 235, 480
    )

    draw_text(
        "Q - QUIT",
        font, RED, 270, 530
    )


# ============================================================
# GAME OVER SOUND
# ============================================================

def end_game():

    global state

    if state != "GAME_OVER":

        state = "GAME_OVER"
        play_sound(crash_sound)


# ============================================================
# SNAKE MOVEMENT
# ============================================================

def move_snake():

    global snake, food, score
    global state, high_score, level, obstacles

    dx, dy = direction

    head = (
        snake[0][0] + dx,
        snake[0][1] + dy
    )

    eating = head == food

    body_to_check = snake if eating else snake[:-1]

    # WALL COLLISION
    if not (
        LEFT <= head[0] < LEFT + COLS * CELL
        and TOP <= head[1] < TOP + ROWS * CELL
    ):

        end_game()
        return

    # SNAKE COLLISION
    if head in body_to_check:

        end_game()
        return

    # OBSTACLE COLLISION
    if head in obstacles:

        end_game()
        return

    snake.insert(0, head)

    if eating:

        score += 10
        high_score = max(high_score, score)

        play_sound(eat_sound)

        # LEVEL PROGRESSION
        new_level = 1 + score // 100

        if new_level > level:

            level = new_level

            obstacles = create_obstacles()

            play_sound(level_sound)

        food = create_food()

        if food is None:
            end_game()

    else:

        snake.pop()


# ============================================================
# KEYBOARD CONTROLS
# ============================================================

def handle_movement(key):

    global next_direction

    if key == pygame.K_UP:

        if next_direction != (0, CELL):
            next_direction = (0, -CELL)

    elif key == pygame.K_DOWN:

        if next_direction != (0, -CELL):
            next_direction = (0, CELL)

    elif key == pygame.K_LEFT:

        if next_direction != (CELL, 0):
            next_direction = (-CELL, 0)

    elif key == pygame.K_RIGHT:

        if next_direction != (-CELL, 0):
            next_direction = (CELL, 0)


# ============================================================
# MAIN GAME LOOP
# ============================================================

def main():

    global state, level, speed, selected
    global direction, next_direction
    global paused, volume

    start_music()

    while True:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                # SOUND ON / OFF
                if event.key == pygame.K_m and state != "GAME_OVER":

                    toggle_sound()
                    continue

                # VOLUME DOWN
                if event.key in (
                    pygame.K_LEFTBRACKET,
                    pygame.K_KP_MINUS
                ):

                    volume = max(0.0, volume - 0.05)

                    if music_channel:
                        music_channel.set_volume(volume * 0.55)

                    continue

                # VOLUME UP
                if event.key in (
                    pygame.K_RIGHTBRACKET,
                    pygame.K_KP_PLUS
                ):

                    volume = min(1.0, volume + 0.05)

                    if music_channel:
                        music_channel.set_volume(volume * 0.55)

                    continue

                # MAIN MENU
                if state == "MENU":

                    if event.key == pygame.K_UP:

                        selected = (selected - 1) % 4
                        play_sound(menu_sound)

                    elif event.key == pygame.K_DOWN:

                        selected = (selected + 1) % 4
                        play_sound(menu_sound)

                    elif event.key == pygame.K_LEFT:

                        if selected == 0:
                            level = max(1, level - 1)

                        elif selected == 1:
                            speed = max(5, speed - 1)

                        elif selected == 2:
                            toggle_sound()

                    elif event.key == pygame.K_RIGHT:

                        if selected == 0:
                            level = min(10, level + 1)

                        elif selected == 1:
                            speed = min(30, speed + 1)

                        elif selected == 2:
                            toggle_sound()

                    elif event.key == pygame.K_RETURN:

                        if selected == 3:
                            start_game()

                        elif selected == 2:
                            toggle_sound()

                        else:
                            selected = 3

                # PLAYING
                elif state == "PLAYING":

                    if event.key in (
                        pygame.K_p,
                        pygame.K_SPACE
                    ):

                        paused = not paused
                        play_sound(pause_sound)

                    elif event.key == pygame.K_ESCAPE:

                        state = "MENU"
                        paused = False
                        start_music()

                    elif not paused:

                        handle_movement(event.key)

                        if event.key in (
                            pygame.K_PLUS,
                            pygame.K_EQUALS,
                            pygame.K_KP_PLUS
                        ):

                            speed = min(30, speed + 1)

                        elif event.key in (
                            pygame.K_MINUS,
                            pygame.K_KP_MINUS
                        ):

                            speed = max(5, speed - 1)

                # GAME OVER
                elif state == "GAME_OVER":

                    if event.key == pygame.K_r:

                        start_game()

                    elif event.key == pygame.K_m:

                        state = "MENU"
                        start_music()

                    elif event.key == pygame.K_q:

                        pygame.quit()
                        sys.exit()

        # GAME UPDATE
        if state == "PLAYING" and not paused:

            direction = next_direction

            move_snake()

        # DISPLAY
        if state == "MENU":

            draw_menu()

        elif state == "PLAYING":

            draw_game()

        elif state == "GAME_OVER":

            draw_game_over()

        pygame.display.flip()

        if state == "PLAYING" and not paused:
            clock.tick(speed)

        else:
            clock.tick(60)


# ============================================================
# RUN GAME
# ============================================================

if __name__ == "__main__":
    main()
