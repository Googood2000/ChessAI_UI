import chess
from typing import Tuple, Optional, Dict
from functools import lru_cache

# Chess Piece Valuation Table
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# Transposition table: cache evaluated positions
TRANSPOSITION_TABLE: Dict[int, Tuple[int, int, int]] = {}  # {zobrist_hash: (score, depth, flag)}

# Position Evaluation Table (Midgame)
POSITION_WEIGHTS = {
    chess.PAWN: [
        0, 0, 0, 0, 0, 0, 0, 0,
        5, 10, 10, -20, -20, 10, 10, 5,
        5, -5, -10, 0, 0, -10, -5, 5,
        0, 0, 0, 20, 20, 0, 0, 0,
        5, 5, 10, 25, 25, 10, 5, 5,
        10, 10, 20, 30, 30, 20, 10, 10,
        50, 50, 50, 50, 50, 50, 50, 50,
        0, 0, 0, 0, 0, 0, 0, 0
    ],
    chess.KNIGHT: [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ],
    chess.BISHOP: [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ],
    chess.ROOK: [
        0, 0, 0, 5, 5, 0, 0, 0,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        5, 5, 5, 5, 5, 5, 5, 5,
        0, 0, 0, 0, 0, 0, 0, 0
    ],
    chess.QUEEN: [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -10, 5, 5, 5, 5, 5, 0, -10,
        0, 0, 5, 5, 5, 5, 0, -5,
        -5, 0, 5, 5, 5, 5, 0, -5,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20
    ],
    chess.KING: [
        20, 30, 10, 0, 0, 10, 30, 20,
        20, 20, 0, 0, 0, 0, 20, 20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30
    ]
}


# def evaluate_board(board: chess.Board) -> int:
#     """
#     Evaluate board position (optimized).
#     Positive values favor White, negative values favor Black.
#     """
#     # Check for terminal game state
#     if board.is_checkmate():
#         return -20000 if board.turn == chess.WHITE else 20000
    
#     if board.is_stalemate() or board.is_insufficient_material():
#         return 0
    
#     score = 0
    
#     # Evaluate the board directly without scanning all 64 squares
#     # Use the board's piece lists instead of iterating over every square
#     for piece_type in chess.PIECE_TYPES:
#         # White pieces
#         white_pieces = board.pieces(piece_type, chess.WHITE)
#         for square in white_pieces:
#             piece_value = PIECE_VALUES[piece_type]
#             position_bonus = POSITION_WEIGHTS[piece_type][square]
#             score += piece_value + position_bonus
        
#         # Black pieces
#         black_pieces = board.pieces(piece_type, chess.BLACK)
#         for square in black_pieces:
#             piece_value = PIECE_VALUES[piece_type]
#             position_bonus = POSITION_WEIGHTS[piece_type][square]
#             score -= piece_value + position_bonus
    
#     return score

# Endgame Position Evaluation Table for the King
KING_ENDGAME = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10,   0,   0, -10, -20, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -30,   0,   0,   0,   0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50
]

# is_endgame function to determine if the game is in the endgame phase
def is_endgame(board: chess.Board) -> bool:
    # Simple heuristic: if both sides have no queens or only one minor piece left, it's likely endgame
    white_queens = len(board.pieces(chess.QUEEN, chess.WHITE))
    black_queens = len(board.pieces(chess.QUEEN, chess.BLACK))
    
    white_minor_pieces = len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.WHITE))
    black_minor_pieces = len(board.pieces(chess.BISHOP, chess.BLACK)) + len(board.pieces(chess.KNIGHT, chess.BLACK))
    
    return (white_queens == 0 and black_queens == 0) or (white_queens == 0 and white_minor_pieces <= 1) or (black_queens == 0 and black_minor_pieces <= 1)

def evaluate_board(board: chess.Board) -> int:
    if board.is_checkmate():
        return -30000 if board.turn == chess.WHITE else 30000
    
    # Improvement: If you're the stronger side, forcing a draw is a punishment; if you're the weaker side, forcing a draw is a reward.
    if board.is_stalemate() or board.is_insufficient_material():
        # Get the current subforce difference (material balance)
        material_balance = 0
        for pt, val in PIECE_VALUES.items():
            material_balance += len(board.pieces(pt, chess.WHITE)) * val
            material_balance -= len(board.pieces(pt, chess.BLACK)) * val
        
        # If the material balance is heavily in favor of one side, a draw is a significant loss for that side and a significant gain for the other.
        if material_balance > 200: return -500 # Significant advantage for White
        if material_balance < -200: return 500 # Significant advantage for Black
        return 0

    score = 0
    endgame = is_endgame(board)
    
    for piece_type in chess.PIECE_TYPES:
        for color in [chess.WHITE, chess.BLACK]:
            pieces = board.pieces(piece_type, color)
            for square in pieces:
                # Material score
                val = PIECE_VALUES[piece_type]
                
                # Positional score (use endgame table for kings if in endgame)
                if piece_type == chess.KING and endgame:
                    pos_bonus = KING_ENDGAME[square if color == chess.WHITE else chess.square_mirror(square)]
                else:
                    pos_bonus = POSITION_WEIGHTS[piece_type][square if color == chess.WHITE else chess.square_mirror(square)]
                
                if color == chess.WHITE:
                    score += (val + pos_bonus)
                else:
                    score -= (val + pos_bonus)
    return score

def _score_move(board: chess.Board, move: chess.Move) -> int:
    """
    Score a move for ordering (MVV-LVA heuristic).
    Prioritize capture moves, especially when a smaller piece captures a larger one.
    """
    try:
        # Prioritize captures
        if board.is_capture(move):
            # For en passant and regular captures
            captured_piece = board.piece_at(move.to_square)
            # For en passant, the captured pawn is on a different square
            if captured_piece is None and board.ep_square == move.to_square:
                captured_piece = board.piece_at(board.ep_square - 8 if board.turn == chess.WHITE else board.ep_square + 8)
            
            attacking_piece = board.piece_at(move.from_square)
            
            if captured_piece and attacking_piece:
                return PIECE_VALUES.get(captured_piece.piece_type, 0) * 100 - PIECE_VALUES.get(attacking_piece.piece_type, 0)
            return 50  # Base score for captures
        
        # Give promotions a high score
        if move.promotion:
            return 1000 + PIECE_VALUES.get(move.promotion, 0)
        
        # Assign low score to other moves
        return 0
    except:
        # Safe fallback: return 0 on exceptions
        return 0


def _order_moves(board: chess.Board, moves: list) -> list:
    """
    Order moves to improve Alpha-Beta pruning efficiency.
    """
    return sorted(moves, key=lambda m: _score_move(board, m), reverse=True)

# Zobrist hashing for transposition table (simplified version)
def get_board_hash(board: chess.Board) -> int:
    # A simple hash function combining key board attributes. In a production engine, you would use a more sophisticated Zobrist hashing with precomputed random numbers for each piece/square combination.
    return hash(board.ep_square) ^ hash(board.castling_rights) ^ hash(board.occupied) ^ hash(board.turn)

# Quiescence search to prevent "horizon effect" by continuing to evaluate capture moves at the leaf nodes of the search tree.
def quiescence_search(board, alpha, beta, is_maximizing):
    """Quiescence search to evaluate "quiet" positions and avoid the horizon effect."""
    stand_pat = evaluate_board(board)
    if is_maximizing:
        if stand_pat >= beta: return beta
        alpha = max(alpha, stand_pat)
    else:
        if stand_pat <= alpha: return alpha
        beta = min(beta, stand_pat)

    for move in board.legal_moves:
        if board.is_capture(move):
            board.push(move)
            score = quiescence_search(board, alpha, beta, not is_maximizing)
            board.pop()
            if is_maximizing:
                if score >= beta: return beta
                alpha = max(alpha, score)
            else:
                if score <= alpha: return alpha
                beta = min(beta, score)
    return alpha if is_maximizing else beta

def minimax_alpha_beta(
    board: chess.Board,
    depth: int,
    alpha: int,
    beta: int,
    is_maximizing: bool,
    max_depth: int = 4
) -> Tuple[int, Optional[chess.Move]]:
    """
    Optimized Minimax algorithm with Alpha-Beta pruning.
    
    Args:
        board: current board state
        depth: current search depth
        alpha: alpha value (lower bound for maximizing side)
        beta: beta value (upper bound for minimizing side)
        is_maximizing: whether this is a maximizing node
        max_depth: maximum search depth
    
    Returns:
        (evaluation score, best move)
    """
    # Check the transposition table (using FEN hash)
    board_hash = get_board_hash(board)
    if board_hash in TRANSPOSITION_TABLE:
        cached_score, cached_depth, cached_flag = TRANSPOSITION_TABLE[board_hash]
        if cached_depth >= depth:
            return cached_score, None

    legal_moves = list(board.legal_moves)

    # Terminal node or maximum depth reached
    if depth == 0:
        eval_score = quiescence_search(board, alpha, beta, is_maximizing)
        # Store in transposition table as a leaf node
        TRANSPOSITION_TABLE[board_hash] = (eval_score, depth, 'exact')
        return eval_score, None
    
    # Order moves to improve pruning efficiency
    legal_moves = _order_moves(board, legal_moves)
    
    best_move = None
    
    if is_maximizing:
        # Maximizing layer (White)
        max_eval = float('-inf')
        for move in legal_moves:
            board.push(move)
            eval_score, _ = minimax_alpha_beta(
                board, depth - 1, alpha, beta, False, max_depth
            )
            board.pop()
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Beta cutoff
        
        # Store in transposition table
        TRANSPOSITION_TABLE[board_hash] = (max_eval, depth, 'exact')
        return max_eval, best_move
    else:
        # Minimizing layer (Black)
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            eval_score, _ = minimax_alpha_beta(
                board, depth - 1, alpha, beta, True, max_depth
            )
            board.pop()
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha cutoff
        
        # Store in transposition table
        TRANSPOSITION_TABLE[board_hash] = (min_eval, depth, 'exact')
        return min_eval, best_move


def get_best_move(board: chess.Board, depth: int = 4, clear_cache: bool = False) -> Optional[chess.Move]:
    """
    Get the best move for the current board position.
    Uses an optimized Minimax algorithm with Alpha-Beta pruning.
    
    Args:
        board: current board state
        depth: search depth (default 4; deeper search is stronger but slower)
        clear_cache: whether to clear the transposition table (default false)
    
    Returns:
        best move, or None if no legal move exists
    """
    # Clear transposition table if requested
    if clear_cache:
        TRANSPOSITION_TABLE.clear()
    
    legal_moves = list(board.legal_moves)
    
    if not legal_moves:
        return None
    
    # If only one legal move exists, return it directly
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # 初始化 Alpha-Beta 值
    alpha = float('-inf')
    beta = float('inf')
    
    # Determine whether this is a maximizing or minimizing position based on current turn
    is_maximizing = (board.turn == chess.WHITE)
    
    _, best_move = minimax_alpha_beta(
        board, depth, alpha, beta, is_maximizing, max_depth=depth
    )
    
    return best_move if best_move else legal_moves[0]
