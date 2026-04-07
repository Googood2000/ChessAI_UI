import pygame
import chess
from ai import get_best_move

class ChessGUI:
    def __init__(self):
        self.screen = pygame.display.set_mode((900, 600))
        pygame.display.set_caption("Chess AI")
        self.clock = pygame.time.Clock()
        self.board = chess.Board()
        self.selected_square = None
        self.possible_moves = []
        self.player_color = None  # 'white' or 'black'
        self.ai_color = None
        self.flipped = True  # Default vertical flip
        self.horizontal_flipped = False  # Added horizontal flip
        self.move_history = []
        self.current_move_index = -1
        self.font = pygame.font.SysFont(None, 24)
        self.piece_font = pygame.font.SysFont('segoeuisymbol', 48)
        self.message = ""
        self.promotion_square = None
        self.select_color()

    def select_color(self):
        # Simple selection: assume white for now, can add menu later
        self.player_color = 'white'
        self.ai_color = 'black'

    def draw_board(self):
        square_size = 60
        for row in range(8):
            for col in range(8):
                color = (255, 206, 158) if (row + col) % 2 == 0 else (209, 139, 71)
                if self.flipped:
                    display_row = 7 - row
                else:
                    display_row = row
                if self.horizontal_flipped:
                    display_col = 7 - col
                else:
                    display_col = col
                x = display_col * square_size
                y = display_row * square_size
                # Highlight selected
                if self.selected_square == chess.square(col, row):
                    color = (255, 255, 0)  # Yellow
                # Highlight possible moves
                elif chess.square(col, row) in self.possible_moves:
                    color = (0, 255, 0)  # Green
                pygame.draw.rect(self.screen, color, (x, y, square_size, square_size))
                piece = self.board.piece_at(chess.square(col, row))
                if piece:
                    piece_symbol = self.get_piece_symbol(piece)
                    text = self.piece_font.render(piece_symbol, True, (0, 0, 0))
                    self.screen.blit(text, (x + 10, y + 10))

    def get_piece_symbol(self, piece):
        symbols = {
            (chess.WHITE, chess.PAWN): '♙',
            (chess.WHITE, chess.KNIGHT): '♘',
            (chess.WHITE, chess.BISHOP): '♗',
            (chess.WHITE, chess.ROOK): '♖',
            (chess.WHITE, chess.QUEEN): '♕',
            (chess.WHITE, chess.KING): '♔',
            (chess.BLACK, chess.PAWN): '♟',
            (chess.BLACK, chess.KNIGHT): '♞',
            (chess.BLACK, chess.BISHOP): '♝',
            (chess.BLACK, chess.ROOK): '♜',
            (chess.BLACK, chess.QUEEN): '♛',
            (chess.BLACK, chess.KING): '♚'
        }
        return symbols[(piece.color, piece.piece_type)]

    def draw_promotion(self):
        if self.promotion_square is not None:
            promotion_buttons = [
                (200, 250, 80, 60, '♕'),
                (290, 250, 80, 60, '♖'),
                (380, 250, 80, 60, '♘'),
                (470, 250, 80, 60, '♗'),
            ]
            mouse_pos = pygame.mouse.get_pos()
            for x, y, w, h, symbol in promotion_buttons:
                color = (200, 200, 200)
                if x <= mouse_pos[0] <= x + w and y <= mouse_pos[1] <= y + h:
                    color = (150, 150, 150)  # Darker on hover
                pygame.draw.rect(self.screen, color, (x, y, w, h))
                txt = self.piece_font.render(symbol, True, (0, 0, 0))
                self.screen.blit(txt, (x + 15, y + 10))

    def draw_buttons(self):
        buttons = [
            ("Undo", 500, 100),
            ("Redo", 500, 150),
            ("Flip Vertical", 500, 200),
            ("Flip Horizontal", 500, 250),
            ("Select White", 500, 300),
            ("Select Black", 500, 350)
        ]
        mouse_pos = pygame.mouse.get_pos()
        for text, x, y in buttons:
            color = (200, 200, 200)
            if x <= mouse_pos[0] <= x + 100 and y <= mouse_pos[1] <= y + 40:
                color = (150, 150, 150)  # Darker on hover
            pygame.draw.rect(self.screen, color, (x, y, 100, 40))
            txt = self.font.render(text, True, (0, 0, 0))
            self.screen.blit(txt, (x + 10, y + 10))

    def handle_click(self, pos):
        if self.promotion_square is not None:
            promotion_buttons = [
                (200, 250, 80, 60, chess.QUEEN, '♕'),
                (290, 250, 80, 60, chess.ROOK, '♖'),
                (380, 250, 80, 60, chess.KNIGHT, '♘'),
                (470, 250, 80, 60, chess.BISHOP, '♗'),
            ]
            for x, y, w, h, piece_type, symbol in promotion_buttons:
                if x <= pos[0] <= x + w and y <= pos[1] <= y + h:
                    move = chess.Move(self.selected_square, self.promotion_square, promotion=piece_type)
                    if move in self.board.legal_moves:
                        self.board.push(move)
                        self.move_history.append(move)
                        self.current_move_index += 1
                        self.message = ""
                        if self.board.turn != (chess.WHITE if self.player_color == 'white' else chess.BLACK):
                            ai_move = get_best_move(self.board)
                            if ai_move:
                                self.board.push(ai_move)
                                self.move_history.append(ai_move)
                                self.current_move_index += 1
                    self.promotion_square = None
                    self.selected_square = None
                    self.possible_moves = []
                    return
            return  # If clicked outside, do nothing

        square_size = 60
        col = pos[0] // square_size
        row = pos[1] // square_size
        if self.flipped:
            row = 7 - row
        if self.horizontal_flipped:
            col = 7 - col
        square = chess.square(col, row)
        if self.selected_square is None:
            if self.board.piece_at(square) and self.board.color_at(square) == (chess.WHITE if self.player_color == 'white' else chess.BLACK):
                self.selected_square = square
                self.possible_moves = [move.to_square for move in self.board.legal_moves if move.from_square == square]
                self.message = ""
        else:
            piece = self.board.piece_at(self.selected_square)
            needs_promotion = False
            if piece and piece.piece_type == chess.PAWN:
                if piece.color == chess.WHITE and chess.square_rank(square) == 7:
                    needs_promotion = True
                elif piece.color == chess.BLACK and chess.square_rank(square) == 0:
                    needs_promotion = True
            if needs_promotion:
                self.promotion_square = square
                self.possible_moves = []
                self.message = "Choose promotion piece"
            else:
                move = chess.Move(self.selected_square, square)
                if move in self.board.legal_moves:
                    self.board.push(move)
                    self.move_history.append(move)
                    self.current_move_index += 1
                    self.message = ""
                    if self.board.turn != (chess.WHITE if self.player_color == 'white' else chess.BLACK):
                        ai_move = get_best_move(self.board)
                        if ai_move:
                            self.board.push(ai_move)
                            self.move_history.append(ai_move)
                            self.current_move_index += 1
                else:
                    self.message = "Invalid move!"
                self.selected_square = None
                self.possible_moves = []

    def draw_status(self):
        status_text = f"Turn: {'White' if self.board.turn == chess.WHITE else 'Black'}"
        if self.board.is_checkmate():
            status_text = "Checkmate!"
        elif self.board.is_stalemate():
            status_text = "Stalemate!"
        elif self.board.is_check():
            status_text = "Check!"
        txt = self.font.render(status_text, True, (0, 0, 0))
        self.screen.blit(txt, (500, 50))
        if self.message:
            msg_txt = self.font.render(self.message, True, (255, 0, 0))
            self.screen.blit(msg_txt, (500, 350))

    def handle_button_click(self, pos):
        if 500 <= pos[0] <= 600:
            if 100 <= pos[1] <= 140:  # Undo
                if self.current_move_index >= 0:
                    self.board.pop()
                    self.current_move_index -= 1
                    self.message = ""
            elif 150 <= pos[1] <= 190:  # Redo
                if self.current_move_index < len(self.move_history) - 1:
                    self.current_move_index += 1
                    self.board.push(self.move_history[self.current_move_index])
                    self.message = ""
            elif 200 <= pos[1] <= 240:  # Vertical flip
                self.flipped = not self.flipped
                self.message = "Board flipped vertically" if self.flipped else "Board vertical orientation restored"
            elif 250 <= pos[1] <= 290:  # Horizontal flip
                self.horizontal_flipped = not self.horizontal_flipped
                self.message = "Board flipped horizontally" if self.horizontal_flipped else "Board horizontal orientation restored"
            elif 300 <= pos[1] <= 340:  # Select White
                self.player_color = 'white'
                self.ai_color = 'black'
                self.board.reset()
                self.move_history = []
                self.current_move_index = -1
                self.selected_square = None
                self.possible_moves = []
                self.message = "Playing as White"
            elif 350 <= pos[1] <= 390:  # Select Black
                self.player_color = 'black'
                self.ai_color = 'white'
                self.board.reset()
                self.move_history = []
                self.current_move_index = -1
                self.selected_square = None
                self.possible_moves = []
                self.message = "Playing as Black"
                self.ai_make_move()  # AI moves first as white

    def ai_make_move(self):
        ai_move = get_best_move(self.board)
        if ai_move:
            self.board.push(ai_move)
            self.move_history.append(ai_move)
            self.current_move_index += 1

    def run(self):
        running = True
        while running:
            self.screen.fill((255, 255, 255))
            self.draw_board()
            self.draw_buttons()
            self.draw_status()
            self.draw_promotion()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    if pos[0] < 480:
                        self.handle_click(pos)
                    else:
                        self.handle_button_click(pos)
            pygame.display.flip()
            self.clock.tick(60)