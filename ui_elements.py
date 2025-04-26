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
                 snap_back=False, action=None):
        self.orientation = orientation
        self.rect = pygame.Rect(x, y, length, 20)
        self.min = min_val
        self.max = max_val
        self.label = label
        self.dragging = False
        self.snap_back = snap_back
        self.knob_d = 8
        self.initial_value = 0 if init_centered else min_val
        self.action=None

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

    def reset_to_initial(self):
        """Reset slider to its initial position"""
        self.value = self.initial_value
        self.update_handle_from_value()

    def do_action(self):
        if self.action:
            self.action(self.value)


