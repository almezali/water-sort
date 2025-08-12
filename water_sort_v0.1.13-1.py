
import pygame
import random
import os

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

# UI Colors
PRIMARY_COLOR = (66, 135, 245) # --primary-color
SECONDARY_COLOR = (80, 80, 80) # --secondary-color
ACCENT_COLOR = (255, 152, 0)   # --accent-color
ERROR_COLOR = (244, 67, 54)    # --error-color
HIGHLIGHT_COLOR = (255, 255, 255, 89) # rgba(255, 255, 255, 0.35)
CONTAINER_BG = (255, 255, 255, 216) # rgba(255, 255, 255, 0.85)
TEXT_COLOR = (51, 51, 51)
BUTTON_TEXT_COLOR = (255, 255, 255)

# Game settings
BOTTLE_WIDTH = 60
BOTTLE_HEIGHT = 180
LIQUID_SEGMENT_HEIGHT = 45 # Each segment is 25% of the bottle height

# Sound effects (placeholders)
# In a real game, you would load actual sound files here

class Bottle:
    def __init__(self, x, y, content, max_capacity=4):
        self.rect = pygame.Rect(x, y, BOTTLE_WIDTH, BOTTLE_HEIGHT)
        self.content = content # List of color indices
        self.max_capacity = max_capacity
        self.is_selected = False
        self.is_hinted = False

    def draw(self, screen):
        # Draw bottle body (glass effect)
        pygame.draw.rect(screen, CONTAINER_BG, self.rect, border_radius=15)
        pygame.draw.rect(screen, PRIMARY_COLOR, self.rect, 3, border_radius=15) # Primary color border

        # Draw bottle neck
        neck_rect = pygame.Rect(self.rect.x + 10, self.rect.y - 10, BOTTLE_WIDTH - 20, 10)
        pygame.draw.rect(screen, PRIMARY_COLOR, neck_rect, border_top_left_radius=10, border_top_right_radius=10)

        # Draw liquid segments
        for i, color_index in enumerate(self.content):
            segment_y = self.rect.y + self.rect.height - (i + 1) * LIQUID_SEGMENT_HEIGHT
            segment_rect = pygame.Rect(self.rect.x + 3, segment_y, BOTTLE_WIDTH - 6, LIQUID_SEGMENT_HEIGHT)
            pygame.draw.rect(screen, LIQUID_COLORS[color_index], segment_rect)

        # Draw selection highlight
        if self.is_selected:
            pygame.draw.rect(screen, ACCENT_COLOR, self.rect, 5, border_radius=15) # Accent color
        elif self.is_hinted:
            pygame.draw.rect(screen, ACCENT_COLOR, self.rect, 5, border_radius=15) # Hint highlight

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
        score_display_x = 200 + self.font.render("Score:", True, TEXT_COLOR).get_width() + 5
        score_display_y = 138
        self.points_animation.append((f"+{points_earned}", score_display_x, score_display_y, pygame.time.get_ticks(), (40, 167, 69))) # Green color

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
        # Draw title
        title_text = self.large_font.render("WATER SORT PUZZLE", True, TEXT_COLOR)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 20))

        # Draw buttons
        button_y = 80
        button_width = 120
        button_height = 40
        button_gap = 10
        total_button_width = 3 * button_width + 2 * button_gap
        start_button_x = (SCREEN_WIDTH - total_button_width) // 2

        start_button_rect = pygame.Rect(start_button_x, button_y, button_width, button_height)
        pygame.draw.rect(screen, PRIMARY_COLOR, start_button_rect, border_radius=8)
        start_text = self.font.render("GAME STARTED" if self.game_started else "START GAME", True, BUTTON_TEXT_COLOR)
        screen.blit(start_text, (start_button_rect.x + (start_button_rect.width - start_text.get_width()) // 2, start_button_rect.y + (start_button_rect.height - start_text.get_height()) // 2))

        new_game_button_rect = pygame.Rect(start_button_x + button_width + button_gap, button_y, button_width, button_height)
        pygame.draw.rect(screen, SECONDARY_COLOR, new_game_button_rect, border_radius=8)
        new_game_text = self.font.render("NEW GAME", True, BUTTON_TEXT_COLOR)
        screen.blit(new_game_text, (new_game_button_rect.x + (new_game_button_rect.width - new_game_text.get_width()) // 2, new_game_button_rect.y + (new_game_button_rect.height - new_game_text.get_height()) // 2))

        hint_button_rect = pygame.Rect(start_button_x + 2 * (button_width + button_gap), button_y, button_width, button_height)
        pygame.draw.rect(screen, ACCENT_COLOR, hint_button_rect, border_radius=8)
        hint_text = self.font.render("HINT", True, BUTTON_TEXT_COLOR)
        screen.blit(hint_text, (hint_button_rect.x + (hint_button_rect.width - hint_text.get_width()) // 2, hint_button_rect.y + (hint_button_rect.height - hint_text.get_height()) // 2))

        # Score Container Background
        score_container_rect = pygame.Rect(50, 130, SCREEN_WIDTH - 100, 80)
        pygame.draw.rect(screen, (255, 255, 255, 100), score_container_rect, border_radius=15)

        # Display Level, Score, High Score
        # Level
        level_label = self.font.render("Level", True, TEXT_COLOR)
        level_value = self.medium_font.render(self.current_level.capitalize(), True, PRIMARY_COLOR)
        screen.blit(level_label, (score_container_rect.x + 20, score_container_rect.y + 10))
        screen.blit(level_value, (score_container_rect.x + 20, score_container_rect.y + 35))

        # Score
        score_label = self.font.render("Score", True, TEXT_COLOR)
        score_value = self.medium_font.render(str(self.score), True, ACCENT_COLOR)
        screen.blit(score_label, (score_container_rect.centerx - score_label.get_width() // 2, score_container_rect.y + 10))
        screen.blit(score_value, (score_container_rect.centerx - score_value.get_width() // 2, score_container_rect.y + 35))

        # High Score
        high_score_label = self.font.render("High Score", True, TEXT_COLOR)
        high_score_value = self.medium_font.render(str(self.high_scores[self.current_level]), True, ACCENT_COLOR)
        screen.blit(high_score_label, (score_container_rect.right - high_score_label.get_width() - 20, score_container_rect.y + 10))
        screen.blit(high_score_value, (score_container_rect.right - high_score_value.get_width() - 20, score_container_rect.y + 35))

        # Level selector
        level_buttons_y = 220
        level_button_width = 80
        level_button_height = 30
        level_gap = 10
        start_level_x = (SCREEN_WIDTH - (3 * level_button_width + 2 * level_gap)) // 2

        levels = ['easy', 'medium', 'hard']
        for i, level in enumerate(levels):
            level_rect = pygame.Rect(start_level_x + i * (level_button_width + level_gap), level_buttons_y, level_button_width, level_button_height)
            is_active = (self.current_level == level)
            
            pygame.draw.rect(screen, PRIMARY_COLOR if is_active else (200, 200, 200), level_rect, border_radius=15)
            pygame.draw.rect(screen, PRIMARY_COLOR, level_rect, 2, border_radius=15)
            
            level_text = self.font.render(level.capitalize(), True, BUTTON_TEXT_COLOR if is_active else TEXT_COLOR)
            screen.blit(level_text, (level_rect.x + (level_rect.width - level_text.get_width()) // 2, level_rect.y + (level_rect.height - level_text.get_height()) // 2))

            # Store rects for click detection
            if level == 'easy': self.easy_level_rect = level_rect
            elif level == 'medium': self.medium_level_rect = level_rect
            elif level == 'hard': self.hard_level_rect = level_rect

        # Moves Counter
        moves_counter_text = self.medium_font.render(f"Moves: {self.moves}", True, TEXT_COLOR)
        screen.blit(moves_counter_text, (SCREEN_WIDTH // 2 - moves_counter_text.get_width() // 2, 260))

        # Draw points animations
        current_time = pygame.time.get_ticks()
        animations_to_remove = []
        for i, (text, x, y, start_time, color) in enumerate(self.points_animation):
            elapsed_time = current_time - start_time
            if elapsed_time < 1000: # Animation duration 1 second
                offset_y = elapsed_time / 1000 * 40 # Move up 40 pixels
                alpha = 255 - (elapsed_time / 1000 * 255) # Fade out
                
                animated_color = (color[0], color[1], color[2], int(alpha))
                points_surface = self.medium_font.render(text, True, animated_color)
                screen.blit(points_surface, (x, y - offset_y))
            else:
                animations_to_remove.append(i)
        
        for i in reversed(animations_to_remove):
            self.points_animation.pop(i)

    def draw_pouring_animation(self, screen):
        if self.pouring_animation:
            from_idx, to_idx, segments_to_pour, color_to_pour, start_time = self.pouring_animation
            elapsed_time = pygame.time.get_ticks() - start_time
            duration = 500 # milliseconds

            if elapsed_time < duration:
                progress = elapsed_time / duration
                
                from_bottle = self.bottles[from_idx]
                to_bottle = self.bottles[to_idx]

                # Calculate start and end points for pouring liquid
                # This needs to be based on the *current* liquid level, not the final one
                # For simplicity, we'll animate from the top of the source bottle
                # to the top of the destination bottle (visually)
                start_x = from_bottle.rect.centerx
                start_y = from_bottle.rect.y + BOTTLE_HEIGHT - (from_bottle.get_top_color_count() * LIQUID_SEGMENT_HEIGHT) # Top of liquid in source

                end_x = to_bottle.rect.centerx
                end_y = to_bottle.rect.y + BOTTLE_HEIGHT - (len(to_bottle.content) * LIQUID_SEGMENT_HEIGHT) # Top of liquid in destination

                # Simple linear interpolation for now
                current_x = start_x + (end_x - start_x) * progress
                current_y = start_y + (end_y - start_y) * progress

                # Draw pouring liquid as a circle (simplified)
                pour_radius = 15
                pygame.draw.circle(screen, LIQUID_COLORS[color_to_pour], (int(current_x), int(current_y)), pour_radius)
            else:
                # Animation finished, clear the animation state
                self.pouring_animation = None

    def show_win_modal(self):
        self.win_modal_active = True

    def draw_win_modal(self, screen):
        if not self.win_modal_active:
            return

        # Darken background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # Semi-transparent black
        screen.blit(overlay, (0, 0))

        # Modal content area
        modal_width = 400
        modal_height = 250
        modal_x = (SCREEN_WIDTH - modal_width) // 2
        modal_y = (SCREEN_HEIGHT - modal_height) // 2
        modal_rect = pygame.Rect(modal_x, modal_y, modal_width, modal_height)
        pygame.draw.rect(screen, (255, 255, 255), modal_rect, border_radius=15)
        pygame.draw.rect(screen, PRIMARY_COLOR, modal_rect, 3, border_radius=15)

        # Title
        title_text = self.large_font.render("Game Over!", True, TEXT_COLOR)
        screen.blit(title_text, (modal_x + (modal_width - title_text.get_width()) // 2, modal_y + 30))

        # Message
        message_lines = [
            f"Congratulations!",
            f"You solved the puzzle in {self.moves} moves!",
            f"Score: {self.score}",
            f"Level Progress: {self.level_progresses[self.current_level]}%"
        ]
        for i, line in enumerate(message_lines):
            line_surface = self.medium_font.render(line, True, TEXT_COLOR)
            screen.blit(line_surface, (modal_x + (modal_width - line_surface.get_width()) // 2, modal_y + 80 + i * 30))

        # Buttons
        new_game_btn_rect = pygame.Rect(modal_x + 50, modal_y + modal_height - 60, 120, 40)
        close_modal_btn_rect = pygame.Rect(modal_x + modal_width - 170, modal_y + modal_height - 60, 120, 40)

        pygame.draw.rect(screen, PRIMARY_COLOR, new_game_btn_rect, border_radius=8)
        new_game_text = self.font.render("New Game", True, BUTTON_TEXT_COLOR)
        screen.blit(new_game_text, (new_game_btn_rect.x + (new_game_btn_rect.width - new_game_text.get_width()) // 2, new_game_btn_rect.y + (new_game_btn_rect.height - new_game_text.get_height()) // 2))

        pygame.draw.rect(screen, ERROR_COLOR, close_modal_btn_rect, border_radius=8)
        close_text = self.font.render("Close", True, BUTTON_TEXT_COLOR)
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
                            button_y = 80
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
            # Background gradient (matching HTML/CSS linear-gradient(45deg, #1a2a6c 0%, #b21f1f 50%, #fdbb2d 100%))
            # Simplified for Pygame, a vertical gradient
            for y in range(SCREEN_HEIGHT):
                # Interpolate colors based on y position
                color1 = (26, 42, 108) # #1a2a6c
                color2 = (178, 31, 31) # #b21f1f
                color3 = (253, 187, 45) # #fdbb2d

                if y < SCREEN_HEIGHT / 2:
                    # From color1 to color2
                    ratio = y / (SCREEN_HEIGHT / 2)
                    r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                    g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                    b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                else:
                    # From color2 to color3
                    ratio = (y - SCREEN_HEIGHT / 2) / (SCREEN_HEIGHT / 2)
                    r = int(color2[0] + (color3[0] - color2[0]) * ratio)
                    g = int(color2[1] + (color3[1] - color2[1]) * ratio)
                    b = int(color2[2] + (color3[2] - color2[2]) * ratio)
                
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


