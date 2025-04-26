import pygame
import sys

# Initialize Pygame
pygame.init()

# Set up the window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Drone Controller")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Button class
class Button:
    def __init__(self, x, y, width, height, text, color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.text = text
        self.action = action

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        font = pygame.font.Font(None, 36)
        text = font.render(self.text, True, BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)

# Slider class
class Slider:
    def __init__(self, x, y, length, min_val, max_val, label,
                 orientation='horizontal', init_centered=False):
        self.orientation = orientation
        self.rect = pygame.Rect(x, y, length, 20)
        self.min = min_val
        self.max = max_val
        self.label = label
        self.dragging = False
        self.knob_d = 8

        # Create rect based on orientation
        if self.orientation == 'horizontal':
            self.rect = pygame.Rect(x, y, length, 20)
            handle_y = y + self.knob_d*1.3  # Center vertically in track
            if init_centered:
                handle_x = x + (length // 2) - self.knob_d
                self.value = 0
            else:
                handle_x = x
                self.value = min_val
            self.handle_rect = pygame.Rect(handle_x, handle_y - self.knob_d, self.knob_d*2, self.knob_d*2)
        else:  # Vertical
            self.rect = pygame.Rect(x, y, 20, length)
            handle_x = x + self.knob_d*1.3  # Center horizontally in track
            if init_centered:
                handle_y = y + (length // 2) - self.knob_d
                self.value = 0
            else:
                handle_y = y + length - self.knob_d*2
                self.value = min_val
            self.handle_rect = pygame.Rect(handle_x - self.knob_d, handle_y, self.knob_d*2, self.knob_d*2)

    def draw(self, surface):
        pygame.draw.rect(surface, GRAY, self.rect)
        pygame.draw.circle(surface, BLACK, self.handle_rect.center, self.knob_d)

        font = pygame.font.Font(None, 24)
        text = font.render(f"{self.label}: {int(self.value)}", True, BLACK)
        surface.blit(text, (self.rect.x, self.rect.y - 30))

    def update_value(self, pos):
        if self.orientation == 'horizontal':
            self.handle_rect.x = max(self.rect.x,
                                   min(pos[0] - self.knob_d,
                                       self.rect.x + self.rect.width - self.knob_d*2))
            self.value = ((self.handle_rect.x - self.rect.x) /
                         (self.rect.width - self.knob_d*2)) * (self.max - self.min) + self.min
        else:  # Vertical
            self.handle_rect.y = max(self.rect.y,
                                    min(pos[1] - self.knob_d,
                                        self.rect.y + self.rect.height - self.knob_d*2))
            # Invert calculation for vertical (top = max, bottom = min)
            self.value = self.max - ((self.handle_rect.y - self.rect.y) /
                                   (self.rect.height - self.knob_d*2)) * (self.max - self.min)

# Create UI elements
buttons = [
    Button(50, 50, 120, 40, "Lift Off", GREEN, "takeoff"),
    Button(200, 50, 120, 40, "Land", RED, "land"),
    Button(350, 50, 200, 40, "Emergency Stop", RED, "emergency"),
    Button(600, 50, 120, 40, "Exit", BLUE, "exit"),
]

sliders = [
    Slider(50, 200, 200, 0, 100, "Throttle", orientation='vertical'),
    Slider(150, 200, 200, -100, 100, "Pitch", orientation='vertical', init_centered=True),
    Slider(50, 450, 200, -100, 100, "Yaw", init_centered=True),
    Slider(50, 550, 200, -100, 100, "Roll", init_centered=True),
]

# Main loop
running = True
current_slider = None

while running:
    screen.fill(WHITE)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check buttons
            for btn in buttons:
                if btn.rect.collidepoint(event.pos):
                    print(f"Button pressed: {btn.text}")
                    # Add drone control calls here
                    # E.g.:
                    # if btn.action == "takeoff": drone.takeoff()
                    # elif btn.action == "land": drone.land()
                    # elif btn.action == "emergency": drone.emergency_stop()
                    if btn.action == "exit":
                        running = False

            # Check sliders
            for slider in sliders:
                if slider.handle_rect.collidepoint(event.pos):
                    current_slider = slider
                    slider.dragging = True

        elif event.type == pygame.MOUSEBUTTONUP:
            if current_slider:
                current_slider.dragging = False
                current_slider = None

        elif event.type == pygame.MOUSEMOTION:
            if current_slider and current_slider.dragging:
                current_slider.update_value(event.pos)
                # Add real-time controls here
                # E.g.:
                # drone.set_throttle(current_slider.value)

    # Draw UI elements
    for btn in buttons:
        btn.draw(screen)

    for slider in sliders:
        slider.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()

