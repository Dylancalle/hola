import pygame
import sys
import numpy as np

# Inicializar Pygame
pygame.init()

# Constantes
BOARD_SIZE = 8
CELL_SIZE = 80   # tamaño de cada celda
BOARD_WIDTH = CELL_SIZE * BOARD_SIZE
BOARD_HEIGHT = CELL_SIZE * BOARD_SIZE
INFO_HEIGHT = 100  # altura de la franja superior
WIDTH, HEIGHT = BOARD_WIDTH, BOARD_HEIGHT + INFO_HEIGHT

DOT_RADIUS = CELL_SIZE // 2 - 5
HIGHLIGHT_RADIUS = CELL_SIZE // 2 - 10

# Colores
BACKGROUND = (0, 128, 0)  # Verde tablero
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GRAY = (200, 200, 200)
HIGHLIGHT = (255, 255, 0, 100)  # Amarillo semitransparente


class OthelloGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Sistemas Inteligentes")
        self.clock = pygame.time.Clock()

        # Logo
        self.logo = pygame.image.load("intro.png")
        self.logo = pygame.transform.scale(self.logo, (80, 80))

        self.reset_game()

    def reset_game(self):
        # Inicializar tablero (0 = vacío, 1 = negro, 2 = blanco)
        self.board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)

        # Configuración inicial
        mid = BOARD_SIZE // 2
        self.board[mid - 1][mid - 1] = 2  # Blanco
        self.board[mid][mid] = 2  # Blanco
        self.board[mid - 1][mid] = 1  # Negro
        self.board[mid][mid - 1] = 1  # Negro

        self.current_player = 1  # Negro empieza
        self.valid_moves = self.get_valid_moves()
        self.game_over = False
        self.winner = None

    def draw_board(self):
        # Fondo tablero
        self.screen.fill(BACKGROUND)

        # Franja negra superior
        pygame.draw.rect(self.screen, BLACK, (0, 0, WIDTH, INFO_HEIGHT))

        # Líneas del tablero (desplazadas hacia abajo)
        for i in range(BOARD_SIZE + 1):
            # Horizontales
            pygame.draw.line(self.screen, BLACK,
                             (0, INFO_HEIGHT + i * CELL_SIZE),
                             (BOARD_WIDTH, INFO_HEIGHT + i * CELL_SIZE), 2)
            # Verticales
            pygame.draw.line(self.screen, BLACK,
                             (i * CELL_SIZE, INFO_HEIGHT),
                             (i * CELL_SIZE, INFO_HEIGHT + BOARD_HEIGHT), 2)

        # Puntos de referencia
        points = [2, 6]
        for i in points:
            for j in points:
                pygame.draw.circle(self.screen, BLACK,
                                   (i * CELL_SIZE, INFO_HEIGHT + j * CELL_SIZE), 5)

        # Fichas
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.board[row][col] != 0:
                    self.draw_piece(row, col)

        # Movimientos válidos
        if not self.game_over:
            for row, col in self.valid_moves:
                center_x = col * CELL_SIZE + CELL_SIZE // 2
                center_y = INFO_HEIGHT + row * CELL_SIZE + CELL_SIZE // 2
                highlight_surface = pygame.Surface((HIGHLIGHT_RADIUS * 2, HIGHLIGHT_RADIUS * 2), pygame.SRCALPHA)
                pygame.draw.circle(highlight_surface, HIGHLIGHT,
                                   (HIGHLIGHT_RADIUS, HIGHLIGHT_RADIUS), HIGHLIGHT_RADIUS)
                self.screen.blit(highlight_surface,
                                 (center_x - HIGHLIGHT_RADIUS, center_y - HIGHLIGHT_RADIUS))

        # Información del juego
        self.draw_game_info()

    def draw_piece(self, row, col):
        center_x = col * CELL_SIZE + CELL_SIZE // 2
        center_y = INFO_HEIGHT + row * CELL_SIZE + CELL_SIZE // 2
        color = BLACK if self.board[row][col] == 1 else WHITE
        pygame.draw.circle(self.screen, color, (center_x, center_y), DOT_RADIUS)
        border_color = WHITE if self.board[row][col] == 1 else BLACK
        pygame.draw.circle(self.screen, border_color, (center_x, center_y), DOT_RADIUS, 2)

    def draw_game_info(self):
        font = pygame.font.SysFont('Arial', 28, bold=True)

        # Contar fichas
        black_count = np.sum(self.board == 1)
        white_count = np.sum(self.board == 2)

        # Turno actual (a la izquierda)
        logo_text = "Hello class, I wanna play a game!"
        player_text = "Turno: " + ("Negro" if self.current_player == 1 else "Blanco")
        player_surface = font.render(player_text, True, WHITE)
        logo_surface = font.render(logo_text, True, RED)
        self.screen.blit(player_surface, (20, 50))
        self.screen.blit(logo_surface, (20, 15))

        # Marcador en el centro
        count_text = f"Negro: {black_count}  Blanco: {white_count}"
        count_surface = font.render(count_text, True, WHITE)
        self.screen.blit(count_surface, (WIDTH // 2 - count_surface.get_width() // 5, 50))

        # Logo a la derecha
        self.screen.blit(self.logo, (WIDTH - 100, 10))

        # Fin de juego
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # Fondo semitransparente
            self.screen.blit(overlay, (0, 0))

            if self.winner == 0:
                result_text = "¡Empate!"
            else:
                result_text = f"¡{'Negro' if self.winner == 1 else 'Blanco'} gana!"

            result_surface = font.render(result_text, True, WHITE)
            restart_surface = font.render("Presiona R para reiniciar", True, WHITE)

            self.screen.blit(result_surface, (WIDTH // 2 - result_surface.get_width() // 2, HEIGHT // 2 - 30))
            self.screen.blit(restart_surface, (WIDTH // 2 - restart_surface.get_width() // 2, HEIGHT // 2 + 30))

    def get_valid_moves(self):
        valid_moves = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.is_valid_move(row, col):
                    valid_moves.append((row, col))
        return valid_moves

    def is_valid_move(self, row, col):
        if self.board[row][col] != 0:
            return False

        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1), (0, 1),
                      (1, -1), (1, 0), (1, 1)]

        opponent = 3 - self.current_player

        for dr, dc in directions:
            r, c = row + dr, col + dc
            found_opponent = False

            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r][c] == opponent:
                found_opponent = True
                r += dr
                c += dc

            if found_opponent and 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r][c] == self.current_player:
                return True

        return False

    def make_move(self, row, col):
        if (row, col) not in self.valid_moves:
            return False

        self.board[row][col] = self.current_player
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1), (0, 1),
                      (1, -1), (1, 0), (1, 1)]

        opponent = 3 - self.current_player

        for dr, dc in directions:
            r, c = row + dr, col + dc
            to_flip = []

            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r][c] == opponent:
                to_flip.append((r, c))
                r += dr
                c += dc

            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r][c] == self.current_player:
                for flip_row, flip_col in to_flip:
                    self.board[flip_row][flip_col] = self.current_player

        self.current_player = 3 - self.current_player
        self.valid_moves = self.get_valid_moves()

        if not self.valid_moves:
            self.current_player = 3 - self.current_player
            self.valid_moves = self.get_valid_moves()

            if not self.valid_moves:
                self.game_over = True
                self.determine_winner()

        return True

    def determine_winner(self):
        black_count = np.sum(self.board == 1)
        white_count = np.sum(self.board == 2)

        if black_count > white_count:
            self.winner = 1
        elif white_count > black_count:
            self.winner = 2
        else:
            self.winner = 0

    def handle_click(self, pos):
        if self.game_over:
            return

        col = pos[0] // CELL_SIZE
        row = (pos[1] - INFO_HEIGHT) // CELL_SIZE  # Compensar franja superior

        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            self.make_move(row, col)

    def run(self):
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Click izquierdo
                        self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # Reiniciar
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:  # Salir
                        running = False

            self.draw_board()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = OthelloGame()
    game.run()
