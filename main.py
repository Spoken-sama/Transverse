import pygame
import sys
import math
import time
import random

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()
pygame.display.set_caption("Simultaneous Canon Animation and Password Game")
clock = pygame.time.Clock()


# Scale factors
SCALE = 1 / 3
SCALECHAR = 1 / 2

# Game state (only for game over of canon part)
game_over = False
password_correct = False
current_rule_index = 0
user_password = ""
rule_feedback = {}

# Sprite groups (initialize here!)
all_sprites = pygame.sprite.Group()
projectiles = pygame.sprite.Group()
canons = pygame.sprite.Group()

# Button setup
font = pygame.font.SysFont(None, 36)
large_font = pygame.font.SysFont(None, 60)
button_width, button_height = 200, 60
button_y_offset = 100

pygame.mixer.init()

# Load background music and cannon sound
pygame.mixer.music.load("/Users/benjamin/PycharmProjects/Transverse/videoplayback.mp3")
#pygame.mixer.music.load("/Users/benjamin/PycharmProjects/Transverse/videoplayback-_1_.mp3")
pygame.mixer.music.play(-1)
bullet_sounds = [
    pygame.mixer.Sound('/Users/benjamin/PycharmProjects/Transverse/Efrei-David.wav'),
    pygame.mixer.Sound('/Users/benjamin/PycharmProjects/Transverse/Efrei.wav')
                ]
running_sound = pygame.mixer.Sound('/Users/benjamin/PycharmProjects/Transverse/Efrei-5.wav')
death_sound = pygame.mixer.Sound('/Users/benjamin/PycharmProjects/Transverse/Efrei-7.wav')
restart_sound = pygame.mixer.Sound('/Users/benjamin/PycharmProjects/Transverse/Efrei-12.wav')
# Set volumes
death_sound.set_volume(0.7)
restart_sound.set_volume(0.5)
running_sound.set_volume(0.2)
pygame.mixer.music.set_volume(0.3)
death_sound.set_volume(0.7)
for sound in bullet_sounds:
    sound.set_volume(0.7)

def draw_button(text, x, y):
    rect = pygame.Rect(x, y, button_width, button_height)
    pygame.draw.rect(screen, (50, 50, 50), rect)
    pygame.draw.rect(screen, (200, 200, 200), rect, 3)
    txt_surf = font.render(text, True, (255, 255, 255))
    txt_rect = txt_surf.get_rect(center=rect.center)
    screen.blit(txt_surf, txt_rect)
    return rect

def reset_canon_game():
    global target, all_sprites, projectiles, canons, game_over, character_animations, canon_sprites, rule_validation_states
    projectiles.empty()
    all_sprites.empty()
    canons.empty()
    canon_sprites = load_canon_sprites()
    character_animations = load_character_sprites()
    target = Character(screen_width // 4, screen_height - 200, character_animations)
    all_sprites.add(target)
    new_canons = pygame.sprite.Group(
        Canon(80, screen_height // 2, 'down', canon_sprites),
        Canon(800, 100, 'right', canon_sprites),
        Canon(1700, screen_height // 2, 'left', canon_sprites, align_topright=True)
    )
    for canon in new_canons:
        canons.add(canon)
        all_sprites.add(canon)
    game_over = False
    rule_validation_states = {}

def load_canon_sprites():
    directions = {
        'down': 'D',
        'left': 'G',
        'right': 'H'
    }
    sprites = {}
    for direction, prefix in directions.items():
        frames = []
        for i in range(1, 6):
            image = pygame.image.load(f"canons/{prefix}{i}.png").convert_alpha()
            scaled = pygame.transform.scale(image, (int(image.get_width() * SCALE), int(image.get_height() * SCALE)))
            frames.append(scaled)
        sprites[direction] = frames
    return sprites

def load_character_sprites():
    anim = {}
    for direction in ['right', 'left']:
        folder = f"run" if direction == 'right' else "run left"
        frames = []
        frame_count = 6 if direction == 'right' else 5
        for i in range(1, frame_count + 1):
            filename = f"{folder}/run{i}.png" if direction == 'right' else f"{folder}/run_left{i}.png"
            img = pygame.image.load(filename).convert_alpha()
            scaled = pygame.transform.scale(img, (int(img.get_width() * SCALECHAR), int(img.get_height() * SCALECHAR)))
            frames.append(scaled)
        anim[direction] = frames
    return anim

original_bullet = pygame.image.load("canons/boulette.png").convert_alpha()
bullet_image = pygame.transform.scale(original_bullet, (int(original_bullet.get_width() * SCALE), int(original_bullet.get_height() * SCALE)))

class Character(pygame.sprite.Sprite):
    def __init__(self, x, y, animations):
        super().__init__()
        self.animations = animations
        self.direction = "right"
        self.index = 0
        self.image = self.animations[self.direction][self.index]
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 400
        self.anim_timer = 0
        self.anim_speed = 0.1
        self.moving = False
        self.running_sound_playing = False  # Track if running sound is playing

    def update(self, dt, keys):
        self.moving = False
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed * dt
            self.direction = "left"
            self.moving = True
        elif keys[pygame.K_RIGHT]:
            self.rect.x += self.speed * dt
            self.direction = "right"
            self.moving = True

        # Ensure the character stays within the screen bounds
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, screen_width)
        self.rect.top = max(self.rect.top, 0)
        self.rect.bottom = min(self.rect.bottom, screen_height)

        if self.moving:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.index = (self.index + 1) % len(self.animations[self.direction])
                self.image = self.animations[self.direction][self.index]
            # Play running sound if not already playing
            if not self.running_sound_playing:
                running_sound.play(-1)  # Loop the sound
                self.running_sound_playing = True
        else:
            self.image = self.animations[self.direction][0]
            self.index = 0
            # Stop running sound when not moving
            if self.running_sound_playing:
                running_sound.stop()
                self.running_sound_playing = False



class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_pos):
        super().__init__()
        self.image = bullet_image
        self.rect = self.image.get_rect(center=(x, y))
        self.x = x
        self.y = y
        dx = target_pos[0] - x
        dy = target_pos[1] - y
        dist = math.hypot(dx, dy)
        if dist == 0:
            dist = 1
        self.vitesse_x = (dx / dist) * 300  # speed
        self.vitesse_y = (dy / dist) * 400

    def update(self, dt):
        self.x += self.vitesse_x * dt
        self.y += self.vitesse_y * dt
        self.rect.center = (int(self.x), int(self.y))
        if (self.rect.right < 0 or self.rect.left > screen_width or
            self.rect.bottom < 0 or self.rect.top > screen_height):
            self.kill()

class Canon(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, sprites, align_topright=False):
        super().__init__()
        self.direction = direction
        self.frames = sprites[direction]
        self.index = 0
        self.image = self.frames[self.index]
        self.align_topright = align_topright
        self.rect = self.image.get_rect()
        if align_topright:
            self.rect.topright = (x, y)
        else:
            self.rect.center = (x, y)
        self.timer = 0
        self.speed = 0.5
        self.fire_rate = 3.0  # Fire every 1 second
        self.last_fired = time.time()

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.speed:
            self.timer = 0
            self.index = (self.index + 1) % len(self.frames)
            self.image = self.frames[self.index]
        center = self.rect.center
        current_time = time.time()
        if current_time - self.last_fired >= self.fire_rate:
            # Play a random bullet sound
            random.choice(bullet_sounds).play()

            # Fire projectile
            projectiles.add(Projectile(center[0], center[1], target.rect.center))
            self.last_fired = current_time
        if self.align_topright:
            self.rect = self.image.get_rect(topright=self.rect.topright)
        else:
            self.rect = self.image.get_rect(center=self.rect.center)

# --- Password Rules ---
def has_length(password):
    return len(password) > 5
def has_upper(password):
    return any(c.isupper() for c in password)
def has_digit(password):
    return any(c.isdigit() for c in password)
def has_special(password):
    return any(c in "!@#$%/-^&*()_+|<>?:" for c in password)
def digit_sum_50(password):
    digits = [int(c) for c in password if c.isdigit()]
    return sum(digits) == 50
def has_roman(password):
    return any(roman in password for roman in ['I', 'V', 'X', 'L', 'C', 'D', 'M'])
def has_element(password):
    elements = ['He', 'Ne', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar']
    return any(elem in password for elem in elements)
def has_grey(password):
    return 'grey' in password.lower()
def has_prime_number(password):
    primes = [str(p) for p in [11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]]
    for p in primes:
        if p in password:
            return True
    return False
def has_pi(password):
    return "3.14159" in password
def roman_sum_multiple_of_35(password):
    roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    roman_sum = 0
    for char in password:
        if char in roman_values:
            roman_sum += roman_values[char]
    return roman_sum % 35 == 0
def is_prime_length(password):
    length = len(password)
    if length < 2:
        return False
    for i in range(2, int(math.sqrt(length)) + 1):
        if length % i == 0:
            return False
    return True
def get_emoji_font_path():
    if sys.platform == "win32":
        # Windows
        return "C:\\Windows\\Fonts\\seguiemj.ttf"
    elif sys.platform == "darwin":
        # macOS
        return "/System/Library/Fonts/Apple Color Emoji.ttc"
    else:
        # Linux or fallback
        return pygame.font.get_default_font()
emoji_font_path = get_emoji_font_path()
emoji_font = pygame.font.Font(emoji_font_path, 24)
def has_current_time(password):
    from datetime import datetime
    current_time = datetime.now().strftime("%H:%M")
    return current_time in password
rules = [
    ("Il doit y avoir plus de 5 caractères", has_length),
    ("Il doit y avoir une majuscule", has_upper),
    ("Il doit y avoir un chiffre", has_digit),
    ("Il doit y avoir un caractère spécial", has_special),
    ("Les chiffres doivent s’additionner pour donner 50", digit_sum_50),
    ("Inclure un chiffre romain", has_roman),
    ("Inclure un élément chimique à 2 lettres (ex: He, Fe...)", has_element),
    ("Les éléments chimiques doivent avoir des numéros atomiques qui additionnent à 200", has_grey),
    ("Inclure un nombre premier à 2 chiffres", has_prime_number),
    ("Contenir la valeur de pi: 3.14159", has_pi),
    ("La somme des chiffres romains doit être un multiple de 35", roman_sum_multiple_of_35),
    ("La longueur du mot de passe doit être un nombre premier", is_prime_length),
    ("Le mot de passe doit inclure l'heure actuelle (hh:mm)", has_current_time),
]
rule_validation_history = {}  # Tracks which rules have ever been validated
all_rules_valid = False  # Tracks if all current rules are valid

def validate_password(password):
    global current_rule_index, rule_validation_history

    results = {}
    for i, (rule_text, rule_func) in enumerate(rules):
        if i <= current_rule_index:  # Only validate rules up to the current index
            try:
                rule_valid = rule_func(password)
                results[i] = rule_valid

                # Update validation history
                if rule_valid:
                    rule_validation_history[i] = True

                # Automatically move to the next rule if the current one is validated
                if i == current_rule_index and rule_valid:
                    current_rule_index += 1
            except:
                results[i] = False

    return results

# --- Integrated Password Game Variables ---
password_font = pygame.font.SysFont(None, 48)
input_rect = pygame.Rect(screen_width // 2 - 200, screen_height // 2 - 50, 400, 80)
input_color_active = pygame.Color('lightskyblue3')
input_color_inactive = pygame.Color('grey')
input_color = input_color_inactive
active = True # Input is active by default
feedback_color_correct = (0, 255, 0)
feedback_color_incorrect = (255, 0, 0)

def draw_password_input():
    pygame.draw.rect(screen, (50, 50, 50, 200), input_rect) # Semi-transparent background
    text_surface = password_font.render("Mot de passe:", True, (220, 220, 220))
    input_surface = password_font.render(user_password, True, (255, 255, 255))
    screen.blit(text_surface, (input_rect.left + 10, input_rect.top - 40))
    pygame.draw.rect(screen, input_color, input_rect, 3)
    screen.blit(input_surface, (input_rect.x + 10, input_rect.y + 10))
def draw_rules():
    font = pygame.font.SysFont(None, 24)
    y_offset = input_rect.bottom + 30

    # Validate to get current states
    rule_results = validate_password(user_password)  # Adjusted to handle a single return value

    for i, (rule_text, _) in enumerate(rules):
        if i <= current_rule_index:  # Show rules up to the current index
            # Rule was previously validated but now fails
            if rule_validation_history.get(i, False) and not rule_results.get(i, False):
                color = feedback_color_incorrect  # Red
            # Rule is currently valid
            elif rule_results.get(i, False):
                color = feedback_color_correct  # Green
            # Rule not yet validated
            else:
                color = (255, 255, 255)  # White

            rule_surface = font.render(f"{i + 1}. {rule_text}", True, color)
            screen.blit(rule_surface, (screen_width // 2 - 200, y_offset))
            y_offset += 20
def update_password_game(events):
    global user_password, active, input_color, current_rule_index, password_correct

    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if input_rect.collidepoint(event.pos):
                active = True
                input_color = input_color_active
            else:
                active = False
                input_color = input_color_inactive

        if event.type == pygame.KEYDOWN and active:
            if event.key == pygame.K_BACKSPACE:
                user_password = user_password[:-1]
            elif event.key == pygame.K_RETURN:
                # Check if the current rule is valid
                if all_rules_valid and current_rule_index < len(rules) - 1:
                    current_rule_index += 1  # Move to the next rule
                elif all_rules_valid and current_rule_index == len(rules) - 1:
                    password_correct = True
            else:
                user_password += event.unicode

    # Continuously validate as the password changes
    if active:
        validate_password(user_password)

# Initial setup
reset_canon_game() # Call reset_canon_game before the main loop
death_sound_played = False
# Main game loop
running = True
while running:
    dt = clock.tick(60) / 1000
    keys = pygame.key.get_pressed()
    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT or (
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        ):
            running = False
        if game_over and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            restart_btn_rect = draw_button("Restart", screen_width // 2 - 100, screen_height // 2 + button_y_offset)
            quit_btn_rect = draw_button("Quit", screen_width // 2 + 100, screen_height // 2 + button_y_offset)

            if restart_btn_rect.collidepoint(mx, my):
                restart_sound.play()  # Play the restart sound here
                reset_canon_game()
                game_over = False
                death_sound_played = False
                current_rule_index = 0
                user_password = ""
                rule_feedback = {}
                password_correct = False
            elif quit_btn_rect.collidepoint(mx, my):
                running = False



    # Update the canon game
    # Update the canon game
    if not game_over and not password_correct:
        target.update(dt, keys)
        canons.update(dt)
        projectiles.update(dt)

        # Collision detection
        if pygame.sprite.spritecollide(target, projectiles, True):
            game_over = True
            # Stop running and background music when player dies
            running_sound.stop()
            pygame.mixer.music.stop()
            # Play death sound if not already played
            if not death_sound_played:
                death_sound.play()
                death_sound_played = True
        # Collision detection
        if pygame.sprite.spritecollide(target, projectiles, True):
            game_over = True


    # Play death sound when game over
    if game_over and not death_sound_played:
        death_sound.play()

        death_sound_played = True

    # Handle password input
    if not game_over and not password_correct:
        update_password_game(events)

    # Draw everything
    screen.fill((20, 20, 20))
    all_sprites.draw(screen)
    projectiles.draw(screen)
    draw_password_input()
    draw_rules()

    if not game_over and not password_correct:
        if not pygame.mixer.music.get_busy():  # Check if music is not playing
            pygame.mixer.music.play(-1)  # Restart background music
    # Game over screen
    if game_over:
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Center the "Game Over" text
        game_over_text = large_font.render("Game Over", True, (255, 0, 0))
        text_rect = game_over_text.get_rect(center=(screen_width // 2, screen_height // 2 - 100))
        screen.blit(game_over_text, text_rect)

        # Draw the buttons using pre-defined rectangles
        restart_btn_rect = draw_button("Restart", screen_width // 2 - button_width // 2,
                                       screen_height // 2 + button_y_offset);
        quit_btn_rect = draw_button("Quit", screen_width // 2 - button_width // 2,
                                    screen_height // 2 + 2 * button_y_offset)


    # Password correct screen
    if password_correct:
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        correct_text = large_font.render("Password Correct!", True, (0, 255, 0))
        text_rect = correct_text.get_rect(center=(screen_width // 2, screen_height // 2 - 50))
        screen.blit(correct_text, text_rect)
        draw_button("Restart", screen_width // 2 - 100, screen_height // 2 + button_y_offset)
        draw_button("Quit", screen_width // 2 + 100, screen_height // 2 + button_y_offset)

    pygame.display.flip()

pygame.quit()
sys.exit()

pygame.quit()
sys.exit()