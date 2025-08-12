import pygame
import random
import os
import math

# Initialize Pygame
pygame.init()
# pygame.mixer.init() # Initialize mixer for sounds

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Water Sort Puzzle v0.1.13 - almezali")

# Colors (matching the HTML/CSS as much as possible)
# These are the primary colors for the liquids
LIQUID_COLORS = [
    (255, 65, 108),  # color-1: #ff416c
    (0, 200, 83),    # color-2: #00c853
    (41, 121, 255),  # color-3: #2979ff
    (170, 0, 255),   # color-4: #aa00ff
    (255, 171, 0),   # color-5: #ffab00
    (0, 188, 212)    # color-6: #00bcd4
]

# UI Colors - Modern Android Material Design 3 inspired
PRIMARY_COLOR = (103, 80, 164)  # Material Purple
SECONDARY_COLOR = (121, 134, 203)  # Material Blue
ACCENT_COLOR = (255, 193, 7)   # Material Amber
ERROR_COLOR = (244, 67, 54)    # Material Red
SUCCESS_COLOR = (76, 175, 80)  # Material Green
SURFACE_COLOR = (255, 255, 255, 120)  # Semi-transparent white
ON_SURFACE_COLOR = (33, 33, 33)  # Dark text
OUTLINE_COLOR = (121, 116, 126)  # Material Outline

# Game settings
BOTTLE_WIDTH = 60
BOTTLE_HEIGHT = 180
LIQUID_SEGMENT_HEIGHT = 45 # Each segment is 25% of the bottle height

def create_glassmorphism_surface(size, alpha=100, border_alpha=150):
    """Create a glassmorphism effect surface"""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    surface.fill((255, 255, 255, alpha))
    return surface

def draw_glassmorphism_rect(surface, rect, alpha=100, border_alpha=150, border_radius=15):
    """Draw a glassmorphism rectangle"""
    glass_surface = create_glassmorphism_surface(rect.size, alpha, border_alpha)
    pygame.draw.rect(glass_surface, (255, 255, 255, border_alpha), glass_surface.get_rect(), 2, border_radius=border_radius)
    surface.blit(glass_surface, rect.topleft)

class Bottle:
    def __init__(self, x, y, content, max_capacity=4):
        self.rect = pygame.Rect(x, y, BOTTLE_WIDTH, BOTTLE_HEIGHT)
        self.content = content # List of color indices
        self.max_capacity = max_capacity
        self.is_selected = False
        self.is_hinted = False

    def draw(self, screen):
        # Draw bottle shadow for depth
        shadow_rect = pygame.Rect(self.rect.x + 3, self.rect.y + 3, BOTTLE_WIDTH, BOTTLE_HEIGHT)
        shadow_surface = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        shadow_surface.fill((0, 0, 0, 30))
        pygame.draw.rect(shadow_surface, (0, 0, 0, 30), shadow_surface.get_rect(), border_radius=15)
        screen.blit(shadow_surface, shadow_rect.topleft)

        # Draw bottle body (glass effect with glassmorphism)
        bottle_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        bottle_surface.fill((255, 255, 255, 60)) # Very light transparent white for glass
        pygame.draw.rect(bottle_surface, (255, 255, 255, 100), bottle_surface.get_rect(), 3, border_radius=15) # Lighter border
        screen.blit(bottle_surface, self.rect.topleft)

        # Draw bottle neck with gradient effect
        neck_rect = pygame.Rect(self.rect.x + 10, self.rect.y - 10, BOTTLE_WIDTH - 20, 10)
        neck_surface = pygame.Surface(neck_rect.size, pygame.SRCALPHA)
        neck_surface.fill(PRIMARY_COLOR)
        pygame.draw.rect(neck_surface, PRIMARY_COLOR, neck_surface.get_rect(), border_top_left_radius=10, border_top_right_radius=10)
        screen.blit(neck_surface, neck_rect.topleft)

        # Draw liquid segments with enhanced visual effects
        for i, color_index in enumerate(self.content):
            segment_y = self.rect.y + self.rect.height - (i + 1) * LIQUID_SEGMENT_HEIGHT
            segment_rect = pygame.Rect(self.rect.x + 3, segment_y, BOTTLE_WIDTH - 6, LIQUID_SEGMENT_HEIGHT)
            
            # Add gradient effect to liquid
            liquid_color = LIQUID_COLORS[color_index]
            darker_color = tuple(max(0, c - 30) for c in liquid_color)
            
            # Draw main liquid segment
            pygame.draw.rect(screen, liquid_color, segment_rect)
            
            # Add highlight on the left side for 3D effect
            highlight_rect = pygame.Rect(segment_rect.x, segment_y, 8, LIQUID_SEGMENT_HEIGHT)
            highlight_color = tuple(min(255, c + 40) for c in liquid_color)
            pygame.draw.rect(screen, highlight_color, highlight_rect)
            
            # Add a slight curve at the top of the liquid if it's the topmost segment
            if i == len(self.content) - 1:
                ellipse_rect = pygame.Rect(self.rect.x + 3, segment_y - 5, BOTTLE_WIDTH - 6, 10)
                pygame.draw.ellipse(screen, liquid_color, ellipse_rect)

        # Draw selection highlight with glow effect
        if self.is_selected:
            glow_surface = pygame.Surface((BOTTLE_WIDTH + 20, BOTTLE_HEIGHT + 20), pygame.SRCALPHA)
            for i in range(10):
                alpha = 255 - (i * 25)
                color = (*ACCENT_COLOR, alpha)
                pygame.draw.rect(glow_surface, color, (10 - i, 10 - i, BOTTLE_WIDTH + 2*i, BOTTLE_HEIGHT + 2*i), 2, border_radius=15 + i)
            screen.blit(glow_surface, (self.rect.x - 10, self.rect.y - 10))
        elif self.is_hinted:
            glow_surface = pygame.Surface((BOTTLE_WIDTH + 20, BOTTLE_HEIGHT + 20), pygame.SRCALPHA)
            for i in range(10):
                alpha = 255 - (i * 25)
                color = (*SUCCESS_COLOR, alpha)
                pygame.draw.rect(glow_surface, color, (10 - i, 10 - i, BOTTLE_WIDTH + 2*i, BOTTLE_HEIGHT + 2*i), 2, border_radius=15 + i)
            screen.blit(glow_surface, (self.rect.x - 10, self.rect.y - 10))

    def get_top_color(self):
        if not self.content: return None
        return self.content[-1]

    def get_top_color_count(self):
        if not self.content: return 0
        top_color = self.get_top_color()
        count = 0
        for color in reversed(self.content):
            if color == top_color:
                count += 1
            else:
                break
        return count

    def is_full(self):
        return len(self.content) == self.max_capacity

    def is_empty(self):
        return len(self.content) == 0

    def is_complete(self):
        if self.is_empty(): return False
        if len(self.content) < self.max_capacity: return False
        first_color = self.content[0]
        return all(color == first_color for color in self.content)

class WaterSortGame:
    def __init__(self):
        self.selected_bottle = None # Index of the selected bottle
        self.moves = 0
        self.game_started = False
        self.current_level = 'easy'
        self.bottles = []
        self.score = 0
        self.high_scores = {'easy': 0, 'medium': 0, 'hard': 0}
        self.level_progresses = {'easy': 0, 'medium': 0, 'hard': 0}

        self.font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 36)
        self.medium_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)

        self.pouring_animation = None # (from_bottle_idx, to_bottle_idx, segments_to_pour, color_to_pour, start_time)
        self.points_animation = [] # (text, x, y, start_time, color)
        self.win_modal_active = False

        self.initialize_game()

    def initialize_game(self):
        num_bottles, num_colors = 0, 0
        if self.current_level == 'easy':
            num_bottles = 5  # 4 color bottles + 1 empty
            num_colors = 3
        elif self.current_level == 'medium':
            num_bottles = 7  # 5 color bottles + 2 empty
            num_colors = 4
        elif self.current_level == 'hard':
            num_bottles = 9  # 6 color bottles + 3 empty
            num_colors = 5

        # Create color segments
        color_segments = []
        for i in range(num_colors):
            for _ in range(4):
                color_segments.append(i)
        random.shuffle(color_segments)

        self.bottles = []
        # Distribute colors into bottles
        for i in range(num_colors):
            bottle_content = []
            for _ in range(4):
                if color_segments: # Ensure there are segments to pop
                    bottle_content.append(color_segments.pop())
            self.bottles.append(Bottle(0, 0, bottle_content))

        # Add empty bottles
        for _ in range(num_bottles - num_colors):
            self.bottles.append(Bottle(0, 0, []))
        random.shuffle(self.bottles) # Shuffle bottles to randomize empty bottle positions

        # Adjust bottle positions dynamically
        self.arrange_bottles()

        self.selected_bottle = None
        self.moves = 0
        self.game_started = False
        self.score = 0
        self.win_modal_active = False

    def arrange_bottles(self):
        total_width = len(self.bottles) * (BOTTLE_WIDTH + 20) - 20 # 20px padding between bottles
        start_x = (SCREEN_WIDTH - total_width) // 2
        for i, bottle in enumerate(self.bottles):
            bottle.rect.x = start_x + i * (BOTTLE_WIDTH + 20)
            bottle.rect.y = SCREEN_HEIGHT - BOTTLE_HEIGHT - 50 # Position from bottom

    def start_game(self):
        self.game_started = True

    def new_game(self):
        self.initialize_game()

    def handle_click(self, pos):
        if self.win_modal_active: # Prevent clicks when modal is active
            return

        if not self.game_started:
            # In Pygame, this would be a UI message, for now just print
            print("Please start the game first!") 
            return

        # Remove any hint highlights
        for bottle in self.bottles:
            bottle.is_hinted = False

        clicked_bottle_index = None
        for i, bottle in enumerate(self.bottles):
            if bottle.rect.collidepoint(pos):
                clicked_bottle_index = i
                break

        if clicked_bottle_index is None: # Clicked outside bottles
            if self.selected_bottle is not None:
                self.bottles[self.selected_bottle].is_selected = False
                self.selected_bottle = None
            return

        if self.selected_bottle is None:
            # Select this bottle if it's not empty
            if not self.bottles[clicked_bottle_index].is_empty():
                self.selected_bottle = clicked_bottle_index
                self.bottles[self.selected_bottle].is_selected = True
        else:
            # Try to pour from selected bottle to this one
            if self.selected_bottle != clicked_bottle_index:
                if self.pour_liquid(self.selected_bottle, clicked_bottle_index):
                    self.moves += 1
                    # Check for win condition
                    if self.check_win_condition():
                        self.handle_level_complete()
            
            # Deselect the bottle
            self.bottles[self.selected_bottle].is_selected = False
            self.selected_bottle = None

    def pour_liquid(self, from_index, to_index):
        from_bottle = self.bottles[from_index]
        to_bottle = self.bottles[to_index]

        if from_bottle.is_empty(): return False
        if to_bottle.is_full(): return False

        color_to_pour = from_bottle.get_top_color()

        if not to_bottle.is_empty() and to_bottle.get_top_color() != color_to_pour:
            return False # Can't mix different colors

        segments_to_pour = from_bottle.get_top_color_count()
        segments_to_pour = min(segments_to_pour, to_bottle.max_capacity - len(to_bottle.content))

        if segments_to_pour == 0: return False

        # Start pouring animation
        self.pouring_animation = (from_index, to_index, segments_to_pour, color_to_pour, pygame.time.get_ticks())
        # self.sound_manager.play_pour()

        # Instead of using a timer, we'll directly complete the pour here
        # and rely on the animation to visually represent the delay.
        # This simplifies the logic and avoids the IndexError.
        self.complete_pour(from_index, to_index, segments_to_pour)

        return True

    def complete_pour(self, from_index, to_index, segments_to_pour):
        from_bottle = self.bottles[from_index]
        to_bottle = self.bottles[to_index]

        # Ensure there's actually liquid to pour before popping
        if from_bottle.is_empty():
            return # Should not happen if pour_liquid checks are correct, but as a safeguard

        for _ in range(segments_to_pour):
            color = from_bottle.content.pop()
            to_bottle.content.append(color)
        
        self.update_score(segments_to_pour)
        self.pouring_animation = None # End animation

        if to_bottle.is_complete():
            # self.sound_manager.play_complete()
            pass # Placeholder for sound

    def check_win_condition(self):
        # Game is won when each bottle either has 4 segments of the same color or is empty
        return all(bottle.is_complete() or bottle.is_empty() for bottle in self.bottles)

    def handle_level_complete(self):
        if self.score > self.high_scores[self.current_level]:
            self.high_scores[self.current_level] = self.score
            # TODO: Save high scores (e.g., to a file)
        
        self.level_progresses[self.current_level] = min(100, self.level_progresses[self.current_level] + 20)
        # TODO: Save level progress

        self.show_win_modal()

    def update_score(self, segments_poured):
        base_points = 10
        multiplier = 1
        if self.current_level == 'medium': multiplier = 1.5
        if self.current_level == 'hard': multiplier = 2

        bonus = segments_poured * 5 if segments_poured > 1 else 0
        points_earned = round((base_points * segments_poured * multiplier) + bonus)
        self.score += points_earned
        
        # Show points animation
        score_display_x = SCREEN_WIDTH // 2
        score_display_y = 200
        self.points_animation.append((f"+{points_earned}", score_display_x, score_display_y, pygame.time.get_ticks(), SUCCESS_COLOR))

    def set_level(self, level):
        self.current_level = level
        self.new_game()

    def show_hint(self):
        if not self.game_started:
            print("Please start the game first!")
            return

        hint_found = False

        # First, try to find a move that completes a bottle
        for from_idx, from_bottle in enumerate(self.bottles):
            if from_bottle.is_empty(): continue
            
            top_color = from_bottle.get_top_color()
            same_color_count = from_bottle.get_top_color_count()
            
            for to_idx, to_bottle in enumerate(self.bottles):
                if from_idx == to_idx: continue
                
                # Check if this move would complete a bottle of the same color
                if not to_bottle.is_empty() and to_bottle.get_top_color() == top_color and \
                   not to_bottle.is_complete() and \
                   len(to_bottle.content) + same_color_count <= to_bottle.max_capacity and \
                   all(color == top_color for color in to_bottle.content):
                    
                    self.bottles[from_idx].is_hinted = True
                    self.bottles[to_idx].is_hinted = True
                    hint_found = True
                    return

        # If no completing move, find any valid move
        if not hint_found:
            for from_idx, from_bottle in enumerate(self.bottles):
                if from_bottle.is_empty(): continue
                
                top_color = from_bottle.get_top_color()
                
                for to_idx, to_bottle in enumerate(self.bottles):
                    if from_idx == to_idx: continue
                    
                    # Check if we can pour into this bottle
                    if to_bottle.is_empty() or (to_bottle.get_top_color() == top_color and not to_bottle.is_full()):
                        self.bottles[from_idx].is_hinted = True
                        self.bottles[to_idx].is_hinted = True
                        hint_found = True
                        return
        
        if not hint_found:
            print("No valid moves found!") # In Pygame, this would be a UI message

    def draw_ui(self, screen):
        # Draw main container background (glassmorphism effect)
        main_container_rect = pygame.Rect(30, 30, SCREEN_WIDTH - 60, SCREEN_HEIGHT - 60)
        draw_glassmorphism_rect(screen, main_container_rect, alpha=80, border_alpha=120, border_radius=25)

        # Draw title with enhanced styling
        title_text = self.large_font.render("WATER SORT PUZZLE", True, ON_SURFACE_COLOR)
        title_shadow = self.large_font.render("WATER SORT PUZZLE", True, (200, 200, 200))
        screen.blit(title_shadow, (SCREEN_WIDTH // 2 - title_text.get_width() // 2 + 2, 52))
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))

        # Draw buttons with glassmorphism
        button_y = 100
        button_width = 120
        button_height = 40
        button_gap = 10
        total_button_width = 3 * button_width + 2 * button_gap
        start_button_x = (SCREEN_WIDTH - total_button_width) // 2

        # Start/Game Started button
        start_button_rect = pygame.Rect(start_button_x, button_y, button_width, button_height)
        button_color = SUCCESS_COLOR if self.game_started else PRIMARY_COLOR
        pygame.draw.rect(screen, button_color, start_button_rect, border_radius=20)
        start_text = self.small_font.render("GAME STARTED" if self.game_started else "START GAME", True, (255, 255, 255))
        screen.blit(start_text, (start_button_rect.x + (start_button_rect.width - start_text.get_width()) // 2, start_button_rect.y + (start_button_rect.height - start_text.get_height()) // 2))

        # New Game button
        new_game_button_rect = pygame.Rect(start_button_x + button_width + button_gap, button_y, button_width, button_height)
        pygame.draw.rect(screen, SECONDARY_COLOR, new_game_button_rect, border_radius=20)
        new_game_text = self.small_font.render("NEW GAME", True, (255, 255, 255))
        screen.blit(new_game_text, (new_game_button_rect.x + (new_game_button_rect.width - new_game_text.get_width()) // 2, new_game_button_rect.y + (new_game_button_rect.height - new_game_text.get_height()) // 2))

        # Hint button
        hint_button_rect = pygame.Rect(start_button_x + 2 * (button_width + button_gap), button_y, button_width, button_height)
        pygame.draw.rect(screen, ACCENT_COLOR, hint_button_rect, border_radius=20)
        hint_text = self.small_font.render("HINT", True, (255, 255, 255))
        screen.blit(hint_text, (hint_button_rect.x + (hint_button_rect.width - hint_text.get_width()) // 2, hint_button_rect.y + (hint_button_rect.height - hint_text.get_height()) // 2))

        # Score Container Background
        score_container_rect = pygame.Rect(main_container_rect.x + 20, button_y + button_height + 20, main_container_rect.width - 40, 80)
        draw_glassmorphism_rect(screen, score_container_rect, alpha=60, border_alpha=100, border_radius=20)

        # Display Level, Score, High Score
        # Level
        level_label = self.small_font.render("Level", True, ON_SURFACE_COLOR)
        level_value = self.medium_font.render(self.current_level.capitalize(), True, PRIMARY_COLOR)
        screen.blit(level_label, (score_container_rect.x + 20, score_container_rect.y + 10))
        screen.blit(level_value, (score_container_rect.x + 20, score_container_rect.y + 35))

        # Score
        score_label = self.small_font.render("Score", True, ON_SURFACE_COLOR)
        score_value = self.medium_font.render(str(self.score), True, ACCENT_COLOR)
        screen.blit(score_label, (score_container_rect.centerx - score_label.get_width() // 2, score_container_rect.y + 10))
        screen.blit(score_value, (score_container_rect.centerx - score_value.get_width() // 2, score_container_rect.y + 35))

        # High Score
        high_score_label = self.small_font.render("High Score", True, ON_SURFACE_COLOR)
        high_score_value = self.medium_font.render(str(self.high_scores[self.current_level]), True, ACCENT_COLOR)
        screen.blit(high_score_label, (score_container_rect.right - high_score_label.get_width() - 20, score_container_rect.y + 10))
        screen.blit(high_score_value, (score_container_rect.right - high_score_value.get_width() - 20, score_container_rect.y + 35))

        # Level selector
        level_buttons_y = score_container_rect.y + score_container_rect.height + 20
        level_button_width = 80
        level_button_height = 35
        level_gap = 10
        start_level_x = (SCREEN_WIDTH - (3 * level_button_width + 2 * level_gap)) // 2

        levels = ['easy', 'medium', 'hard']
        for i, level in enumerate(levels):
            level_rect = pygame.Rect(start_level_x + i * (level_button_width + level_gap), level_buttons_y, level_button_width, level_button_height)
            is_active = (self.current_level == level)
            
            button_color = PRIMARY_COLOR if is_active else OUTLINE_COLOR
            pygame.draw.rect(screen, button_color, level_rect, border_radius=18)
            
            level_text = self.font.render(level.capitalize(), True, (255, 255, 255) if is_active else ON_SURFACE_COLOR)
            screen.blit(level_text, (level_rect.x + (level_rect.width - level_text.get_width()) // 2, level_rect.y + (level_rect.height - level_text.get_height()) // 2))

            # Store rects for click detection
            if level == 'easy': self.easy_level_rect = level_rect
            elif level == 'medium': self.medium_level_rect = level_rect
            elif level == 'hard': self.hard_level_rect = level_rect

        # Moves Counter
        moves_counter_text = self.medium_font.render(f"Moves: {self.moves}", True, ON_SURFACE_COLOR)
        screen.blit(moves_counter_text, (SCREEN_WIDTH // 2 - moves_counter_text.get_width() // 2, level_buttons_y + level_button_height + 15))

        # Draw points animations
        current_time = pygame.time.get_ticks()
        animations_to_remove = []
        for i, (text, x, y, start_time, color) in enumerate(self.points_animation):
            elapsed_time = current_time - start_time
            if elapsed_time < 1500: # Animation duration 1.5 seconds
                offset_y = elapsed_time / 1500 * 60 # Move up 60 pixels
                alpha = 255 - (elapsed_time / 1500 * 255) # Fade out
                
                # Create animated text with glow effect
                points_surface = self.medium_font.render(text, True, color)
                glow_surface = self.medium_font.render(text, True, (255, 255, 255, int(alpha // 2)))
                screen.blit(glow_surface, (x - points_surface.get_width() // 2 + 1, y - offset_y + 1))
                screen.blit(points_surface, (x - points_surface.get_width() // 2, y - offset_y))
            else:
                animations_to_remove.append(i)
        
        for i in reversed(animations_to_remove):
            self.points_animation.pop(i)

    def draw_pouring_animation(self, screen):
        if self.pouring_animation:
            from_idx, to_idx, segments_to_pour, color_to_pour, start_time = self.pouring_animation
            elapsed_time = pygame.time.get_ticks() - start_time
            duration = 800 # milliseconds

            if elapsed_time < duration:
                progress = elapsed_time / duration
                
                from_bottle = self.bottles[from_idx]
                to_bottle = self.bottles[to_idx]

                # Calculate start and end points for pouring liquid
                start_x = from_bottle.rect.centerx
                start_y = from_bottle.rect.y + BOTTLE_HEIGHT - (from_bottle.get_top_color_count() * LIQUID_SEGMENT_HEIGHT)

                end_x = to_bottle.rect.centerx
                end_y = to_bottle.rect.y + BOTTLE_HEIGHT - (len(to_bottle.content) * LIQUID_SEGMENT_HEIGHT)

                # Create a parabolic arc for more realistic pouring
                mid_x = (start_x + end_x) / 2
                mid_y = min(start_y, end_y) - 50  # Arc height
                
                # Quadratic Bezier curve
                t = progress
                current_x = (1-t)**2 * start_x + 2*(1-t)*t * mid_x + t**2 * end_x
                current_y = (1-t)**2 * start_y + 2*(1-t)*t * mid_y + t**2 * end_y

                # Draw pouring liquid with trail effect
                pour_radius = 12
                trail_length = 5
                for i in range(trail_length):
                    trail_t = max(0, t - i * 0.05)
                    trail_x = (1-trail_t)**2 * start_x + 2*(1-trail_t)*trail_t * mid_x + trail_t**2 * end_x
                    trail_y = (1-trail_t)**2 * start_y + 2*(1-trail_t)*trail_t * mid_y + trail_t**2 * end_y
                    trail_alpha = 255 - (i * 50)
                    trail_color = (*LIQUID_COLORS[color_to_pour], trail_alpha)
                    trail_surface = pygame.Surface((pour_radius * 2, pour_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(trail_surface, trail_color, (pour_radius, pour_radius), pour_radius - i)
                    screen.blit(trail_surface, (int(trail_x) - pour_radius, int(trail_y) - pour_radius))
            else:
                # Animation finished, clear the animation state
                self.pouring_animation = None

    def show_win_modal(self):
        self.win_modal_active = True

    def draw_win_modal(self, screen):
        if not self.win_modal_active:
            return

        # Darken background with blur effect
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200)) # Semi-transparent black
        screen.blit(overlay, (0, 0))

        # Modal content area with glassmorphism
        modal_width = 450
        modal_height = 300
        modal_x = (SCREEN_WIDTH - modal_width) // 2
        modal_y = (SCREEN_HEIGHT - modal_height) // 2
        modal_rect = pygame.Rect(modal_x, modal_y, modal_width, modal_height)
        
        draw_glassmorphism_rect(screen, modal_rect, alpha=150, border_alpha=200, border_radius=25)

        # Title
        title_text = self.large_font.render("Congratulations!", True, SUCCESS_COLOR)
        screen.blit(title_text, (modal_x + (modal_width - title_text.get_width()) // 2, modal_y + 30))

        # Message
        message_lines = [
            f"Puzzle solved in {self.moves} moves!",
            f"Score: {self.score}",
            f"Level Progress: {self.level_progresses[self.current_level]}%"
        ]
        for i, line in enumerate(message_lines):
            line_surface = self.medium_font.render(line, True, ON_SURFACE_COLOR)
            screen.blit(line_surface, (modal_x + (modal_width - line_surface.get_width()) // 2, modal_y + 100 + i * 35))

        # Buttons
        new_game_btn_rect = pygame.Rect(modal_x + 60, modal_y + modal_height - 70, 140, 45)
        close_modal_btn_rect = pygame.Rect(modal_x + modal_width - 200, modal_y + modal_height - 70, 140, 45)

        pygame.draw.rect(screen, PRIMARY_COLOR, new_game_btn_rect, border_radius=22)
        new_game_text = self.font.render("New Game", True, (255, 255, 255))
        screen.blit(new_game_text, (new_game_btn_rect.x + (new_game_btn_rect.width - new_game_text.get_width()) // 2, new_game_btn_rect.y + (new_game_btn_rect.height - new_game_text.get_height()) // 2))

        pygame.draw.rect(screen, ERROR_COLOR, close_modal_btn_rect, border_radius=22)
        close_text = self.font.render("Close", True, (255, 255, 255))
        screen.blit(close_text, (close_modal_btn_rect.x + (close_modal_btn_rect.width - close_text.get_width()) // 2, close_modal_btn_rect.y + (close_modal_btn_rect.height - close_text.get_height()) // 2))

        self.new_game_btn_rect = new_game_btn_rect # Store for click detection
        self.close_modal_btn_rect = close_modal_btn_rect # Store for click detection

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left click
                        if self.win_modal_active:
                            if self.new_game_btn_rect.collidepoint(event.pos):
                                self.new_game()
                                self.win_modal_active = False
                            elif self.close_modal_btn_rect.collidepoint(event.pos):
                                self.win_modal_active = False
                                running = False # Optionally close game
                        else:
                            # Check button clicks
                            button_y = 100 # Adjusted button_y
                            button_width = 120
                            button_height = 40
                            button_gap = 10
                            total_button_width = 3 * button_width + 2 * button_gap
                            start_button_x = (SCREEN_WIDTH - total_button_width) // 2

                            start_button_rect = pygame.Rect(start_button_x, button_y, button_width, button_height)
                            new_game_button_rect = pygame.Rect(start_button_x + button_width + button_gap, button_y, button_width, button_height)
                            hint_button_rect = pygame.Rect(start_button_x + 2 * (button_width + button_gap), button_y, button_width, button_height)

                            if start_button_rect.collidepoint(event.pos):
                                self.start_game()
                            elif new_game_button_rect.collidepoint(event.pos):
                                self.new_game()
                            elif hint_button_rect.collidepoint(event.pos):
                                self.show_hint()
                            elif hasattr(self, 'easy_level_rect') and self.easy_level_rect.collidepoint(event.pos):
                                self.set_level('easy')
                            elif hasattr(self, 'medium_level_rect') and self.medium_level_rect.collidepoint(event.pos):
                                self.set_level('medium')
                            elif hasattr(self, 'hard_level_rect') and self.hard_level_rect.collidepoint(event.pos):
                                self.set_level('hard')
                            else:
                                self.handle_click(event.pos)

            # Drawing
            # Background gradient (modern Android-like with multiple color stops)
            for y in range(SCREEN_HEIGHT):
                if y < SCREEN_HEIGHT * 0.3:
                    # Top section: Light purple to blue
                    ratio = y / (SCREEN_HEIGHT * 0.3)
                    color_start = (230, 220, 255)  # Light purple
                    color_end = (200, 230, 255)    # Light blue
                elif y < SCREEN_HEIGHT * 0.7:
                    # Middle section: Light blue to light green
                    ratio = (y - SCREEN_HEIGHT * 0.3) / (SCREEN_HEIGHT * 0.4)
                    color_start = (200, 230, 255)  # Light blue
                    color_end = (220, 255, 230)    # Light green
                else:
                    # Bottom section: Light green to light yellow
                    ratio = (y - SCREEN_HEIGHT * 0.7) / (SCREEN_HEIGHT * 0.3)
                    color_start = (220, 255, 230)  # Light green
                    color_end = (255, 250, 220)    # Light yellow

                r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
                g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
                b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
                
                pygame.draw.line(SCREEN, (r, g, b), (0, y), (SCREEN_WIDTH, y))

            self.draw_ui(SCREEN)
            for bottle in self.bottles:
                bottle.draw(SCREEN)
            
            self.draw_pouring_animation(SCREEN)
            self.draw_win_modal(SCREEN)

            pygame.display.flip()

        pygame.quit()

if __name__ == '__main__':
    game = WaterSortGame()
    game.run()

