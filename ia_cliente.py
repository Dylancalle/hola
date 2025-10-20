# ia_cliente.py
import pygame
import sys
import numpy as np
import socket
import json
import threading
import time
import random # Para posibles movimientos si la búsqueda falla

# =========================================================
# CLASE OthelloAI (MOTOR DEL JUEGO Y ALGORITMO DE BÚSQUEDA)
# =========================================================

class OthelloAI:
    def __init__(self, board_size=8, depth=4):
        self.board_size = board_size
        self.max_depth = depth
        # Mapeo de colores para el algoritmo
        self.PLAYER_COLOR = 1 # Se establecerá después de la conexión
        self.OPPONENT_COLOR = 2 # 3 - self.PLAYER_COLOR

        # Pesos para la función de evaluación
        # Valores heurísticos para Othello/Reversi:
        # 1. Puntuación: +1 para ficha propia.
        # 2. Movilidad: +X por cada movimiento legal.
        # 3. Estabilidad: Peso en las esquinas, bordes.
        self.WEIGHT_MATRIX = np.array([
            [100, -20, 10, 5, 5, 10, -20, 100],
            [-20, -50, -2, -2, -2, -2, -50, -20],
            [10, -2, -1, -1, -1, -1, -2, 10],
            [5, -2, -1, 0, 0, -1, -2, 5],
            [5, -2, -1, 0, 0, -1, -2, 5],
            [10, -2, -1, -1, -1, -1, -2, 10],
            [-20, -50, -2, -2, -2, -2, -50, -20],
            [100, -20, 10, 5, 5, 10, -20, 100]
        ])

    def set_player_color(self, color):
        self.PLAYER_COLOR = color
        self.OPPONENT_COLOR = 3 - color

    # --- Funciones de Othello (copia de servidor/juego01) ---

    def _get_valid_moves(self, board, player):
        valid_moves = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self._is_valid_move(board, row, col, player):
                    valid_moves.append((row, col))
        return valid_moves

    def _is_valid_move(self, board, row, col, player):
        if board[row][col] != 0:
            return False
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        opponent = 3 - player
        for dr, dc in directions:
            r, c = row + dr, col + dc
            found_opponent = False
            while 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == opponent:
                found_opponent = True
                r += dr
                c += dc
            if found_opponent and 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == player:
                return True
        return False

    def _make_move(self, board, row, col, player):
        new_board = np.copy(board)
        new_board[row][col] = player
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        opponent = 3 - player

        for dr, dc in directions:
            r, c = row + dr, col + dc
            to_flip = []
            while 0 <= r < self.board_size and 0 <= c < self.board_size and new_board[r][c] == opponent:
                to_flip.append((r, c))
                r += dr
                c += dc
            if 0 <= r < self.board_size and 0 <= c < self.board_size and new_board[r][c] == player:
                for flip_row, flip_col in to_flip:
                    new_board[flip_row][flip_col] = player
        return new_board

    # --- Función de Evaluación (Heurística) ---

    def _evaluate(self, board):
        """
        Función de evaluación heurística.
        Evalúa el estado del tablero desde la perspectiva de self.PLAYER_COLOR.
        Mayor valor = mejor para el jugador de la IA.
        """
        score = 0
        
        # 1. Puntuación de Posición (Estabilidad y Valor de las celdas)
        # Se beneficia de ocupar esquinas y celdas con alto peso
        player_score_matrix = np.sum((board == self.PLAYER_COLOR) * self.WEIGHT_MATRIX)
        opponent_score_matrix = np.sum((board == self.OPPONENT_COLOR) * self.WEIGHT_MATRIX)
        
        score += (player_score_matrix - opponent_score_matrix) * 0.8
        
        # 2. Movilidad (Número de movimientos legales disponibles)
        # Un mayor número de movimientos legales suele ser una ventaja
        player_moves = len(self._get_valid_moves(board, self.PLAYER_COLOR))
        opponent_moves = len(self._get_valid_moves(board, self.OPPONENT_COLOR))
        
        # Evitar división por cero
        if player_moves + opponent_moves != 0:
            mobility = (player_moves - opponent_moves) / (player_moves + opponent_moves)
            score += mobility * 20 # Ponderación alta para la movilidad
            
        # 3. Puntuación Bruta (para desempate o juego tardío)
        player_count = np.sum(board == self.PLAYER_COLOR)
        opponent_count = np.sum(board == self.OPPONENT_COLOR)
        score += (player_count - opponent_count) * 0.1
        
        return score

    # --- Algoritmo Minimax con Poda Alfa-Beta ---

    def _minimax(self, board, depth, alpha, beta, is_maximizing_player):
        """
        Implementación recursiva del algoritmo Minimax con Poda Alfa-Beta.
        """
        if depth == 0:
            return self._evaluate(board), None

        # Verificar si el juego terminó (no hay movimientos válidos para ambos)
        player_to_move = self.PLAYER_COLOR if is_maximizing_player else self.OPPONENT_COLOR
        opponent_to_move = self.OPPONENT_COLOR if is_maximizing_player else self.PLAYER_COLOR

        valid_moves = self._get_valid_moves(board, player_to_move)
        
        if not valid_moves:
            # Si el jugador actual no tiene movimientos, el turno pasa al oponente
            opponent_moves = self._get_valid_moves(board, opponent_to_move)
            
            if not opponent_moves:
                # Si ninguno tiene movimientos, es el final del juego
                return self._evaluate(board), None # Evaluar el estado final
            else:
                # Simular un "paso de turno"
                return self._minimax(board, depth - 1, alpha, beta, not is_maximizing_player)

        best_move = valid_moves[0] # Inicializar con el primer movimiento válido

        if is_maximizing_player:
            max_eval = -np.inf
            for move in valid_moves:
                new_board = self._make_move(board, move[0], move[1], player_to_move)
                # El siguiente estado es del oponente (minimizing)
                eval, _ = self._minimax(new_board, depth - 1, alpha, beta, False) 
                
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                    
                alpha = max(alpha, max_eval)
                if beta <= alpha:
                    break # Poda Beta
            return max_eval, best_move
        else: # Minimizing player
            min_eval = np.inf
            for move in valid_moves:
                new_board = self._make_move(board, move[0], move[1], player_to_move)
                # El siguiente estado es del jugador IA (maximizing)
                eval, _ = self._minimax(new_board, depth - 1, alpha, beta, True) 

                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                    
                beta = min(beta, min_eval)
                if beta <= alpha:
                    break # Poda Alfa
            return min_eval, best_move
            
    def get_best_move(self, current_board_list):
        """Función pública para iniciar la búsqueda."""
        # Convertir lista a numpy array para la AI
        current_board = np.array(current_board_list)
        
        # Buscar el mejor movimiento
        print(f"🧠 IA pensando... (Profundidad: {self.max_depth})")
        start_time = time.time()
        
        # Maximizing player es siempre la IA (self.PLAYER_COLOR)
        eval, best_move = self._minimax(
            board=current_board, 
            depth=self.max_depth, 
            alpha=-np.inf, 
            beta=np.inf, 
            is_maximizing_player=True
        )
        
        end_time = time.time()
        
        print(f"✅ Búsqueda terminada en {end_time - start_time:.2f}s. Evaluación: {eval:.2f}. Movimiento: {best_move}")
        
        return best_move


# =========================================================
# CLASE ExpectimaxClient (CLIENTE DE RED SIMPLIFICADO)
# =========================================================

# Constantes (simplificadas, no se necesita PyGame aquí)
WIDTH, HEIGHT = 800, 800
BOARD_SIZE = 8
CELL_SIZE = WIDTH // BOARD_SIZE

class ExpectimaxClient:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.socket = None
        self.player_color = None
        self.game_state = None
        self.connected = False
        self.connection_status = "Desconectado"
        self.ai = OthelloAI(depth=5) # Crear la instancia de la IA
        self.last_move_time = 0

    def connect(self):
        # ... (Mantener la lógica de conexión similar a cliente.py)
        try:
            self.connection_status = "Conectando..."
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(0.5)
            self.connected = True
            self.connection_status = "Conectado al servidor"
            print("✅ ¡Conectado al servidor!")
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            return True
        except Exception as e:
            self.connection_status = f"Error de conexión: {str(e)}"
            print(f"❌ {self.connection_status}")
            return False
            
    def receive_messages(self):
        # ... (Mantener la lógica de recepción similar a cliente.py)
        buffer = ""
        while self.connected:
            try:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    print("📭 Servidor cerró la conexión")
                    self.connected = False
                    break
                buffer += data
                while '\n' in buffer:
                    message_str, buffer = buffer.split('\n', 1)
                    if message_str.strip():
                        try:
                            message = json.loads(message_str)
                            self.handle_message(message)
                        except json.JSONDecodeError as e:
                            print(f"❌ Error decodificando JSON: {e}")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"❌ Error recibiendo mensajes: {e}")
                self.connected = False
                break

    def handle_message(self, message):
        msg_type = message.get('type')
        print(f"📨 Mensaje recibido del servidor: {msg_type}")

        if msg_type == 'welcome':
            self.player_color = message['player_color']
            self.ai.set_player_color(self.player_color) # Configurar la IA con el color
            print(f"🎯 Eres el jugador: {'NEGRO' if self.player_color == 1 else 'BLANCO'}")

        elif msg_type == 'game_start' or msg_type == 'game_update':
            self.game_state = message['game_state']
            
            # Llamar a la lógica de la IA
            self.process_turn()
            
        elif msg_type == 'move_response':
            if not message['success']:
                print(f"❌ Movimiento fallido (IA): {message['message']}")

    def send_message(self, message):
        # ... (Mantener la lógica de envío similar a cliente.py)
        if not self.connected:
            return False
        try:
            message_str = json.dumps(message) + '\n'
            self.socket.send(message_str.encode('utf-8'))
            print(f"📤 Mensaje IA enviado: {message['type']}")
            return True
        except Exception as e:
            self.connected = False
            return False

    def send_move(self, row, col):
        message = {'type': 'move', 'row': row, 'col': col}
        return self.send_message(message)

    def process_turn(self):
        """Lógica para que la IA decida y juegue."""
        if not self.game_state:
            return

        if self.game_state['game_over']:
            print("🛑 Juego terminado")
            return

        if self.game_state['current_player'] == self.player_color:
            current_time = time.time()
            if current_time - self.last_move_time < 1.0: # Esperar un poco para no saturar
                time.sleep(1.0 - (current_time - self.last_move_time))
            
            print("🚀 Es mi turno. Calculando mejor movimiento...")
            
            # 1. Obtener el tablero y movimientos
            board_list = self.game_state['board']
            valid_moves = self.game_state['valid_moves'] # Usar los que da el servidor para mayor seguridad

            if not valid_moves:
                print("⚠️ No hay movimientos válidos, pasar turno (el servidor lo maneja)")
                return
            
            # 2. Obtener el mejor movimiento de la IA
            best_move = self.ai.get_best_move(board_list)
            
            # Si la búsqueda de la IA no encuentra un movimiento válido (debería encontrarlo)
            if best_move not in [(m[0], m[1]) for m in valid_moves]:
                # Fallback: Elegir un movimiento aleatorio de la lista del servidor
                best_move = random.choice(valid_moves)
                print(f"⚠️ Fallback: Usando movimiento aleatorio: {best_move}")

            # 3. Enviar el movimiento
            row, col = best_move
            self.send_move(row, col)
            self.last_move_time = time.time()
        else:
            print("⏳ Es turno del oponente, esperando...")


    def run(self):
        if not self.connect():
            print("⚠️ No se pudo conectar al servidor, saliendo.")
            sys.exit()

        # El cliente IA se queda en el bucle de recepción en su propio hilo.
        # El hilo principal solo se usa para mantener el programa vivo.
        try:
            while self.connected:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Cliente IA detenido")
        finally:
            if self.socket:
                self.socket.close()
            sys.exit()


if __name__ == "__main__":
    print("=== 🤖 CLIENTE IA OTHELLO (MINIMAX ALPHA-BETA) ===")
    host = input("Servidor [localhost]: ").strip() or 'localhost'
    port_input = input("Puerto [5555]: ").strip()
    port = int(port_input) if port_input.isdigit() else 5555

    client = ExpectimaxClient(host, port)
    client.run()