import pygame

from ui_colors import *

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

    def do_action(self):
        if self.action:
            self.action()


# Slider class
class Slider:
    def __init__(self, x, y, length, min_val, max_val, label,
                 orientation='horizontal', init_centered=False,
                 snap_back=False, action=None, rounding=0):
        self.orientation = orientation
        self.rect = pygame.Rect(x, y, length, 20)
        self.min = min_val
        self.max = max_val
        self.label = label
        self.dragging = False
        self.snap_back = snap_back
        self.knob_d = 8
        self.initial_value = 0 if init_centered else min_val
        self.action=action
        self.rounding = rounding

        # Create rect based on orientation
        if self.orientation == 'horizontal':
            self.rect = pygame.Rect(x, y, length, 20)
            handle_y = y + self.knob_d*1.3  # Center vertically in track
            if init_centered:
                handle_x = x + (length // 2) - self.knob_d
            else:
                handle_x = x
            self.handle_rect = pygame.Rect(handle_x, handle_y - self.knob_d, self.knob_d*2, self.knob_d*2)
        else:  # Vertical
            self.rect = pygame.Rect(x, y, 20, length)
            handle_x = x + self.knob_d*1.3  # Center horizontally in track
            if init_centered:
                handle_y = y + (length // 2) - self.knob_d
            else:
                handle_y = y + length - self.knob_d*2
            self.handle_rect = pygame.Rect(handle_x - self.knob_d, handle_y, self.knob_d*2, self.knob_d*2)
        self.value = self.initial_value
        self.update_handle_from_value()

    def update_handle_from_value(self):
        """Update handle position based on current value"""
        if self.orientation == 'horizontal':
            ratio = (self.value - self.min) / (self.max - self.min)
            self.handle_rect.x = self.rect.x + ratio * (self.rect.width - self.knob_d*2)
        else:
            ratio = (self.max - self.value) / (self.max - self.min)
            self.handle_rect.y = self.rect.y + ratio * (self.rect.height - self.knob_d*2)

    def draw(self, surface):
        pygame.draw.rect(surface, GRAY, self.rect)
        pygame.draw.circle(surface, BLACK, self.handle_rect.center, self.knob_d)

        font = pygame.font.Font(None, 24)
        text = font.render(f"{self.label}: {round(self.value, self.rounding)}", True, BLACK)
        surface.blit(text, (self.rect.x, self.rect.y - 30))

    def set_value(self, val):
        self.value = val
        self.update_handle_from_value()

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

    def reset_to_initial(self):
        """Reset slider to its initial position"""
        self.value = self.initial_value
        self.update_handle_from_value()
        self.do_action()

    def do_action(self):
        if self.action:
            self.action(self.value)

class Ticker:
    def __init__(self, x, y, min_val, max_val, initial_val, label_text="", step=1):
        self.min_val = min_val
        self.max_val = max_val
        self.value = max(min(initial_val, max_val), min_val)
        self.label_text = label_text
        self.step = step

        # Component dimensions
        self.display_width = 60
        self.display_height = 40
        self.button_size = 20
        self.label_padding = 10

        # Font setup
        self.font = pygame.font.SysFont('Arial', 24)

        # Create label surface first to calculate positions
        self.label_surface = self.font.render(self.label_text, True, (0, 0, 0))
        self.label_rect = self.label_surface.get_rect(topleft=(x, y + self.display_height//4))

        # Create component rectangles (adjusted for label)
        self.display_rect = pygame.Rect(
            x + self.label_rect.width + self.label_padding,
            y,
            self.display_width,
            self.display_height
        )
        self.up_button_rect = pygame.Rect(
            self.display_rect.right,
            y,
            self.button_size,
            self.button_size
        )
        self.down_button_rect = pygame.Rect(
            self.display_rect.right,
            y + self.button_size,
            self.button_size,
            self.button_size
        )

        # Arrow polygon points
        margin = 5
        # Up arrow points (top, bottom-left, bottom-right)
        self.up_arrow = [
            (self.up_button_rect.centerx, self.up_button_rect.top + margin),
            (self.up_button_rect.left + margin, self.up_button_rect.bottom - margin),
            (self.up_button_rect.right - margin, self.up_button_rect.bottom - margin)
        ]
        # Down arrow points (bottom, top-left, top-right)
        self.down_arrow = [
            (self.down_button_rect.centerx, self.down_button_rect.bottom - margin),
            (self.down_button_rect.left + margin, self.down_button_rect.top + margin),
            (self.down_button_rect.right - margin, self.down_button_rect.top + margin)
        ]

    def draw(self, surface):
        # Draw label
        surface.blit(self.label_surface, self.label_rect)

        # Draw display background and border
        pygame.draw.rect(surface, (255, 255, 255), self.display_rect)  # White background
        pygame.draw.rect(surface, (0, 0, 0), self.display_rect, 2)     # Black border

        # Draw up button
        pygame.draw.rect(surface, (200, 200, 200), self.up_button_rect)  # Gray background
        pygame.draw.rect(surface, (0, 0, 0), self.up_button_rect, 2)    # Black border
        pygame.draw.polygon(surface, (0, 0, 0), self.up_arrow)          # Black arrow

        # Draw down button
        pygame.draw.rect(surface, (200, 200, 200), self.down_button_rect)
        pygame.draw.rect(surface, (0, 0, 0), self.down_button_rect, 2)
        pygame.draw.polygon(surface, (0, 0, 0), self.down_arrow)

        # Render and center text
        text_surface = self.font.render(str(round(self.value, 2)), True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.display_rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if self.up_button_rect.collidepoint(mouse_pos):
                self.value = min(self.value + self.step, self.max_val)
            elif self.down_button_rect.collidepoint(mouse_pos):
                self.value = max(self.value - self.step, self.min_val)

